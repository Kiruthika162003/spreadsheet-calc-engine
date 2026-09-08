from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.values import ErrorValue

WORLD = {
    (0, 0): 1.0,
    (1, 0): 2.0,
    (2, 0): 3.0,
    (0, 1): 4.0,
    (1, 1): 5.0,
    (2, 1): 6.0,
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(parse_formula(formula), lookup, full_table)


class TestPairedSums:
    def test_sum_of_squared_differences(self):
        # (1-4)^2 + (2-5)^2 + (3-6)^2 = 9 + 9 + 9.
        assert run("=SUMXMY2(A1:A3, B1:B3)") == 27.0

    def test_sum_of_differences_of_squares(self):
        assert run("=SUMX2MY2(A1:A3, B1:B3)") == -63.0

    def test_sum_of_sums_of_squares(self):
        assert run("=SUMX2PY2(A1:A3, B1:B3)") == 91.0


class TestAlignmentAndSkips:
    def test_mismatched_lengths_are_refused(self):
        outcome = run("=SUMXMY2(A1:A3, B1:B2)")
        assert outcome.code == "#N/A"
        assert "computes noise" in outcome.note

    def test_a_text_pair_is_skipped(self):
        world = dict(WORLD)
        world[(1, 0)] = "n/a"

        def skip_lookup(ref: CellRef):
            return world.get(ref.key())

        # The middle pair drops out; only rows 1 and 3 count.
        outcome = evaluate(
            parse_formula("=SUMXMY2(A1:A3, B1:B3)"),
            skip_lookup,
            full_table,
        )
        assert outcome == 18.0

    def test_an_error_poisons_the_result(self):
        world = dict(WORLD)
        world[(0, 0)] = ErrorValue(code="#DIV/0!", note="x")

        def poison_lookup(ref: CellRef):
            return world.get(ref.key())

        outcome = evaluate(
            parse_formula("=SUMXMY2(A1:A3, B1:B3)"),
            poison_lookup,
            full_table,
        )
        assert outcome.code == "#DIV/0!"

    def test_a_scalar_argument_is_refused(self):
        outcome = run("=SUMXMY2(5, B1:B3)")
        assert outcome.code == "#VALUE!"
