from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

WORLD = {
    (0, 0): 3.0, (1, 0): 4.0, (2, 0): 5.0,
    (0, 1): 10.0, (1, 1): 20.0, (2, 1): 30.0,
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestIntAndSqrt:
    def test_int_floors_toward_negative_infinity(self):
        assert run("=INT(2.9)") == 2.0
        assert run("=INT(0-2.1)") == -3.0

    def test_sqrt_keeps_the_ledger_real(self):
        assert run("=SQRT(144)") == 12.0
        outcome = run("=SQRT(0-4)")
        assert outcome.code == "#NUM!"
        assert "not on the menu of any ledger" in outcome.note


class TestSnapping:
    def test_ceiling_and_floor_snap_to_multiples(self):
        assert run("=CEILING(4.3, 0.5)") == 4.5
        assert run("=FLOOR(4.3, 0.5)") == 4.0
        assert run("=CEILING(123, 10)") == 130.0

    def test_zero_significance_is_a_division_in_costume(self):
        outcome = run("=CEILING(5, 0)")
        assert outcome.code == "#DIV/0!"
        assert "wearing a costume" in outcome.note

    def test_mismatched_signs_have_no_defensible_answer(self):
        outcome = run("=CEILING(5, 0-2)")
        assert outcome.code == "#NUM!"


class TestProducts:
    def test_product_over_scalars_and_ranges(self):
        assert run("=PRODUCT(2, 3, 4)") == 24.0
        assert run("=PRODUCT(A1:A3)") == 60.0

    def test_sumproduct_is_the_weighted_sum_idiom(self):
        assert run("=SUMPRODUCT(A1:A3, B1:B3)") == (
            3 * 10 + 4 * 20 + 5 * 30
        )

    def test_mismatched_shapes_are_refused(self):
        outcome = run("=SUMPRODUCT(A1:A3, B1:B2)")
        assert outcome.code == "#VALUE!"
        assert "equal shapes" in outcome.note

    def test_the_empty_product_multiplies_nothing(self):
        assert run("=PRODUCT(D1:D3)").code == "#VALUE!"
