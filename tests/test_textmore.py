from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.textmore import text_split

WORLD = {(0, 0): "a\tb\nc"}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(parse_formula(formula), lookup, full_table)


class TestCut:
    def test_before_and_after_the_first_delimiter(self):
        assert run('=TEXTBEFORE("a-b-c", "-")') == "a"
        assert run('=TEXTAFTER("a-b-c", "-")') == "b-c"

    def test_a_negative_instance_counts_from_the_end(self):
        assert (
            run('=TEXTAFTER("path/to/file", "/", -1)')
            == "file"
        )
        assert (
            run('=TEXTBEFORE("path/to/file", "/", -1)')
            == "path/to"
        )

    def test_an_absent_delimiter_is_not_the_whole_string(self):
        outcome = run('=TEXTBEFORE("nodelim", "-")')
        assert outcome.code == "#N/A"
        assert "failed split" in outcome.note

    def test_an_instance_beyond_the_occurrences(self):
        outcome = run('=TEXTAFTER("a-b", "-", 5)')
        assert outcome.code == "#N/A"

    def test_an_empty_delimiter_cuts_nowhere(self):
        outcome = run('=TEXTBEFORE("abc", "")')
        assert outcome.code == "#VALUE!"


class TestConcatAndClean:
    def test_concat_joins_with_no_separator(self):
        assert run('=CONCAT("a", 1, "b")') == "a1b"

    def test_clean_strips_control_characters(self):
        # A1 holds "a\tb\nc" with a tab and a newline.
        assert run("=CLEAN(A1)") == "abc"


class TestTextSplitHelper:
    def test_it_splits_all_pieces(self):
        assert text_split("a,b,c", ",") == ["a", "b", "c"]

    def test_an_empty_delimiter_is_refused(self):
        with pytest.raises(Invalid) as caught:
            text_split("abc", "")
        assert "different function" in str(caught.value)
