from __future__ import annotations

import pytest

from gridiron.errors import Unparseable
from gridiron.tokens import lex


def kinds_and_texts(formula: str) -> list[tuple[str, str]]:
    return [
        (token.kind, token.text) for token in lex(formula)
    ]


class TestTheSurface:
    def test_a_full_formula_tokenizes(self):
        assert kinds_and_texts('SUM(A1:B2, 3.5) & "x"') == [
            ("word", "SUM"),
            ("operator", "("),
            ("word", "A1"),
            ("operator", ":"),
            ("word", "B2"),
            ("operator", ","),
            ("number", "3.5"),
            ("operator", ")"),
            ("operator", "&"),
            ("string", "x"),
        ]

    def test_positions_are_part_of_truth(self):
        tokens = lex("A1 + B2")
        assert [token.position for token in tokens] == [0, 3, 5]

    def test_spaces_separate_and_vanish(self):
        assert kinds_and_texts("  1  +  2  ") == [
            ("number", "1"),
            ("operator", "+"),
            ("number", "2"),
        ]


class TestLongestMatch:
    def test_two_char_operators_never_split(self):
        assert kinds_and_texts("A1<=B2") == [
            ("word", "A1"),
            ("operator", "<="),
            ("word", "B2"),
        ]
        assert kinds_and_texts("A1<>B2")[1] == ("operator", "<>")

    def test_bare_comparisons_still_work(self):
        assert kinds_and_texts("A1<B2")[1] == ("operator", "<")


class TestStrings:
    def test_doubled_quotes_escape(self):
        tokens = lex('"say ""hi"""')
        assert tokens[0].text == 'say "hi"'

    def test_the_unclosed_string_names_its_start(self):
        with pytest.raises(Unparseable) as caught:
            lex('1 + "dangling')
        assert "position 4 never closes" in str(caught.value)


class TestRefusals:
    def test_the_unknown_character_is_not_autocorrected(self):
        with pytest.raises(Unparseable) as caught:
            lex("A1 @ B2")
        assert "position 3" in str(caught.value)
        assert "autocorrect" in str(caught.value)

    def test_an_empty_formula_parses_to_nothing(self):
        with pytest.raises(Unparseable):
            lex("   ")

    def test_decimals_keep_one_dot(self):
        assert kinds_and_texts("1.5.2") == [
            ("number", "1.5"),
            ("number", ".2"),
        ]
