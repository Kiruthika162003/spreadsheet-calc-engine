from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

TABLE = {
    (0, 0): "apples", (0, 1): 1.20, (0, 2): 40.0,
    (1, 0): "bread", (1, 1): 2.50, (1, 2): 15.0,
    (2, 0): "cheese", (2, 1): 6.00, (2, 2): 8.0,
    (4, 0): 10.0, (5, 0): 20.0, (6, 0): 30.0,
    (8, 0): 30.0, (9, 0): 10.0, (10, 0): 20.0,
}


def lookup(ref: CellRef):
    return TABLE.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestExactByDefault:
    def test_the_exact_lookup_finds_its_row(self):
        assert run('=VLOOKUP("bread", A1:C3, 2)') == 2.50
        assert run('=VLOOKUP("cheese", A1:C3, 3)') == 8.0

    def test_the_miss_renders_the_key(self):
        outcome = run('=VLOOKUP("mangoes", A1:C3, 2)')
        assert outcome.code == "#N/A"
        assert "mangoes" in outcome.note

    def test_the_column_is_checked_against_the_table(self):
        outcome = run('=VLOOKUP("bread", A1:C3, 9)')
        assert outcome.code == "#VALUE!"
        assert "outside the table's 3 column(s)" in outcome.note


class TestApproximateOnRequest:
    def test_the_stair_lookup_takes_the_floor(self):
        assert run("=VLOOKUP(25, A5:A7, 1, TRUE)") == 20.0
        assert run("=VLOOKUP(10, A5:A7, 1, TRUE)") == 10.0

    def test_below_the_first_stair_is_a_miss(self):
        assert run("=VLOOKUP(5, A5:A7, 1, TRUE)").code == "#N/A"

    def test_unsorted_keys_are_refused_with_the_rows_named(self):
        outcome = run("=VLOOKUP(15, A9:A11, 1, TRUE)")
        assert outcome.code == "#VALUE!"
        assert "plausible wrong answer would be worse" in (
            outcome.note
        )


class TestIndexAndMatch:
    def test_the_classic_pair_composes(self):
        assert run('=INDEX(B1:C3, MATCH("cheese", A1:A3), 1)') == (
            6.00
        )

    def test_match_reports_one_based_position(self):
        assert run('=MATCH("bread", A1:A3)') == 2.0

    def test_index_checks_its_borders(self):
        outcome = run("=INDEX(A1:C3, 4, 1)")
        assert outcome.code == "#VALUE!"
        assert "outside the 3x3 table" in outcome.note

    def test_a_scalar_where_a_table_belongs_is_named(self):
        assert run('=VLOOKUP("x", A1, 1)').code == "#VALUE!"
