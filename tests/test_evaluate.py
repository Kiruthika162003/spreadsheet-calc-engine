from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.values import ErrorValue, is_error

WORLD = {
    (0, 0): 10.0,
    (1, 0): 4.0,
    (0, 1): "label",
    (1, 1): ErrorValue(code="#REF!"),
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def no_functions(_name: str):
    return None


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, no_functions
    )


class TestArithmeticOverTheWorld:
    def test_refs_resolve_and_arithmetic_flows(self):
        assert run("=A1+A2") == 14.0
        assert run("=A1/A2") == 2.5
        assert run("=A1-A2*2") == 2.0

    def test_the_famous_case_evaluates_to_four(self):
        assert run("=-2^2") == 4.0

    def test_percent_and_power(self):
        assert run("=50%") == 0.5
        assert run("=2^10") == 1024.0

    def test_the_empty_cell_is_zero_in_arithmetic(self):
        assert run("=Z99+5") == 5.0


class TestErrorFlow:
    def test_the_poisoned_cell_poisons_its_dependents_only(self):
        poisoned = run("=B2+1")
        assert is_error(poisoned)
        assert poisoned.code == "#REF!"
        assert run("=A1+1") == 11.0

    def test_text_arithmetic_refuses_to_launder(self):
        assert run("=B1*2").code == "#VALUE!"

    def test_a_bare_range_in_scalar_position_is_refused(self):
        outcome = run("=A1:B2")
        assert outcome.code == "#VALUE!"
        assert "survives review" in outcome.note

    def test_the_unknown_name_and_function_say_name(self):
        assert run("=TAXRATE").code == "#NAME?"
        assert run("=NOPE(1)").code == "#NAME?"


class TestComparisonsAndText:
    def test_numbers_sort_before_text_before_booleans(self):
        assert run('=1<"a"') is True
        assert run('="a"<TRUE') is True
        assert run("=TRUE>99") is True

    def test_text_comparison_ignores_case(self):
        assert run('="Apple"="APPLE"') is True

    def test_concat_renders_like_the_grid_does(self):
        assert run('=A1&" items"') == "10 items"
        assert run('=""&TRUE') == "TRUE"

    def test_overflowing_power_is_a_num_error(self):
        assert run("=10^400").code == "#NUM!"
