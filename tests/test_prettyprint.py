from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.prettyprint import pretty_formula
from gridiron.refs import CellRef

WORLD = {
    (0, 0): 6.0,
    (1, 0): 3.0,
    (2, 0): 2.0,
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def value(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestMinimalParentheses:
    def test_a_flat_chain_needs_none(self):
        assert pretty_formula("=A1+A2+A3") == "=A1+A2+A3"

    def test_multiplication_over_addition_stays_bare(self):
        assert (
            pretty_formula("=A1*A2+A3") == "=A1*A2+A3"
        )

    def test_addition_under_multiplication_wraps(self):
        assert (
            pretty_formula("=(A1+A2)*A3") == "=(A1+A2)*A3"
        )

    def test_the_paste_wrapper_is_stripped(self):
        assert (
            pretty_formula("=((A1*2)+A2)") == "=A1*2+A2"
        )


class TestTheSubtractionTrap:
    def test_a_right_side_sum_keeps_its_parentheses(self):
        formula = "=A1-(A2+A3)"
        assert pretty_formula(formula) == "=A1-(A2+A3)"
        assert value(formula) == 1.0

    def test_a_left_side_sum_does_not_need_them(self):
        assert (
            pretty_formula("=(A1+A2)-A3") == "=A1+A2-A3"
        )

    def test_division_guards_its_right_side(self):
        formula = "=A1/(A2*A3)"
        assert pretty_formula(formula) == "=A1/(A2*A3)"
        assert value(formula) == 1.0


class TestPowersAndUnary:
    def test_a_left_power_stays_bare_under_left_assoc(self):
        assert pretty_formula("=(2^3)^2") == "=2^3^2"
        assert pretty_formula("=2^3^2") == "=2^3^2"

    def test_a_right_power_keeps_its_parentheses(self):
        formula = "=2^(3^2)"
        assert pretty_formula(formula) == "=2^(3^2)"
        assert value(formula) == 512.0

    def test_unary_over_a_sum_wraps(self):
        formula = "=-(A1+A2)"
        assert pretty_formula(formula) == "=-(A1+A2)"
        assert value(formula) == -9.0

    def test_unary_over_an_atom_stays_bare(self):
        assert pretty_formula("=-A1") == "=-A1"


class TestRoundTripMeaning:
    def test_pretty_reparses_to_the_same_value(self):
        for formula in (
            "=A1-(A2-A3)",
            "=(A1-A2)/A3+A1",
            "=A1*(A2+A3)-A1/A2",
            "=-(A1-A2)*A3",
        ):
            once = value(formula)
            twice = value(pretty_formula(formula))
            assert once == twice

    def test_calls_keep_comma_separated_arguments(self):
        assert (
            pretty_formula("=SUM(A1*2, A2+A3)")
            == "=SUM(A1*2, A2+A3)"
        )
