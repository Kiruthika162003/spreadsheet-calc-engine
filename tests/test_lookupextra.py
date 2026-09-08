from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

WORLD = {
    (0, 0): "acct-1",
    (1, 0): "acct-2",
    (2, 0): "acct-1",
    (3, 0): "acct-3",
    (0, 1): "Ada",
    (1, 1): "Grace",
    (2, 1): "Alan",
    (3, 1): "Edsger",
    (0, 3): "Q1",
    (0, 4): "Q2",
    (0, 5): "Q3",
    (1, 3): 100.0,
    (1, 4): 120.0,
    (1, 5): 90.0,
    (2, 3): 0.61,
    (2, 4): 0.64,
    (2, 5): 0.58,
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestXlookup:
    def test_separate_columns_kill_the_counting_bug(self):
        assert (
            run('=XLOOKUP("acct-2", A1:A4, B1:B4)')
            == "Grace"
        )

    def test_case_folds_like_the_rest_of_the_grid(self):
        assert (
            run('=XLOOKUP("ACCT-3", A1:A4, B1:B4)')
            == "Edsger"
        )

    def test_the_fallback_is_an_argument_not_a_wrapper(self):
        assert (
            run(
                '=XLOOKUP("acct-9", A1:A4, B1:B4, '
                '"nobody")'
            )
            == "nobody"
        )

    def test_without_a_fallback_the_key_is_named(self):
        outcome = run('=XLOOKUP("acct-9", A1:A4, B1:B4)')
        assert outcome.code == "#N/A"
        assert "acct-9" in outcome.note

    def test_last_match_answers_the_ledger_question(self):
        first = run(
            '=XLOOKUP("acct-1", A1:A4, B1:B4, "x", '
            '"FIRST")'
        )
        last = run(
            '=XLOOKUP("acct-1", A1:A4, B1:B4, "x", '
            '"LAST")'
        )
        assert first == "Ada"
        assert last == "Alan"

    def test_unequal_columns_are_the_bug_reborn(self):
        outcome = run(
            '=XLOOKUP("acct-1", A1:A4, B1:B3)'
        )
        assert outcome.code == "#VALUE!"
        assert "counting bug reborn" in outcome.note

    def test_the_direction_must_be_stated(self):
        outcome = run(
            '=XLOOKUP("acct-1", A1:A4, B1:B4, "x", 1)'
        )
        assert outcome.code == "#VALUE!"
        assert "FIRST or LAST" in outcome.note

    def test_a_wide_key_range_is_refused(self):
        outcome = run(
            '=XLOOKUP("acct-1", A1:B4, B1:B4)'
        )
        assert outcome.code == "#VALUE!"
        assert "single columns" in outcome.note


class TestHlookup:
    def test_the_sideways_table_reads_by_row(self):
        assert run('=HLOOKUP("Q2", D1:F3, 2)') == 120.0
        assert run('=HLOOKUP("Q3", D1:F3, 3)') == 0.58

    def test_a_missing_quarter_names_itself(self):
        outcome = run('=HLOOKUP("Q4", D1:F3, 2)')
        assert outcome.code == "#N/A"
        assert "Q4" in outcome.note

    def test_a_row_outside_the_table_is_counted(self):
        outcome = run('=HLOOKUP("Q1", D1:F3, 9)')
        assert outcome.code == "#VALUE!"
        assert "3 row(s)" in outcome.note
