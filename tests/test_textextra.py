from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

WORLD = {
    (0, 0): "alpha",
    (1, 0): "beta",
    (2, 0): None,
    (3, 0): 42.0,
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestSubstitute:
    def test_every_occurrence_by_default(self):
        assert (
            run('=SUBSTITUTE("a-b-c", "-", "+")') == "a+b+c"
        )

    def test_the_instance_picks_one(self):
        assert (
            run('=SUBSTITUTE("a-b-c", "-", "+", 2)')
            == "a-b+c"
        )

    def test_an_instance_past_the_last_changes_nothing(self):
        assert (
            run('=SUBSTITUTE("a-b-c", "-", "+", 9)')
            == "a-b-c"
        )

    def test_a_zero_instance_is_refused(self):
        outcome = run('=SUBSTITUTE("abc", "b", "x", 0)')
        assert outcome.code == "#VALUE!"
        assert "count from one" in outcome.note


class TestFindAndSearch:
    def test_find_is_case_sensitive(self):
        assert run('=FIND("B", "abBc")') == 3.0
        outcome = run('=FIND("z", "abc")')
        assert outcome.code == "#VALUE!"
        assert "position zero is a lie" in outcome.note

    def test_search_folds_case_and_stays_literal(self):
        assert run('=SEARCH("b", "aBc")') == 2.0
        outcome = run('=SEARCH("a*c", "abc")')
        assert outcome.code == "#VALUE!"

    def test_the_start_offsets_the_hunt(self):
        assert run('=FIND("a", "banana", 3)') == 4.0

    def test_a_start_outside_the_haystack(self):
        outcome = run('=FIND("a", "hi", 9)')
        assert outcome.code == "#VALUE!"
        assert "outside the haystack" in outcome.note


class TestReplaceAndRept:
    def test_replace_is_positional(self):
        assert (
            run('=REPLACE("2024-01", 6, 2, "12")')
            == "2024-12"
        )

    def test_rept_builds_rulers(self):
        assert run('=REPT("ab", 3)') == "ababab"

    def test_a_cell_is_not_a_novel(self):
        outcome = run('=REPT("x", 20000)')
        assert outcome.code == "#VALUE!"
        assert "not a novel" in outcome.note


class TestTextjoin:
    def test_ranges_join_in_reading_order(self):
        assert (
            run('=TEXTJOIN(", ", TRUE, A1:A4)')
            == "alpha, beta, 42"
        )

    def test_keeping_empties_keeps_their_seats(self):
        assert (
            run('=TEXTJOIN("-", FALSE, A1:A4)')
            == "alpha-beta--42"
        )

    def test_the_flag_must_be_stated(self):
        outcome = run('=TEXTJOIN("-", 1, A1:A2)')
        assert outcome.code == "#VALUE!"
        assert "stated, not implied" in outcome.note


class TestTheSmallOnes:
    def test_proper_capitalizes_at_boundaries(self):
        assert (
            run('=PROPER("o\'brien-smith was here")')
            == "O'Brien-Smith Was Here"
        )

    def test_exact_is_the_case_sensitive_equality(self):
        assert run('=EXACT("Ab", "Ab")') is True
        assert run('=EXACT("Ab", "ab")') is False

    def test_char_and_code_round_trip_ascii(self):
        assert run("=CHAR(65)") == "A"
        assert run('=CODE("A")') == 65.0

    def test_char_refuses_the_unprintable(self):
        outcome = run("=CHAR(7)")
        assert outcome.code == "#VALUE!"
        assert "printable ASCII" in outcome.note

    def test_value_parses_what_the_lexer_would(self):
        assert run('=VALUE(" 12.5 ")') == 12.5
        outcome = run('=VALUE("1.234,56")')
        assert outcome.code == "#VALUE!"
        assert "locale module owns that war" in outcome.note
