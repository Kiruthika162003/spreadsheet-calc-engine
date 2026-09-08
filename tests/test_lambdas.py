from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.lambdas import LambdaRegistry
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

WORLD = {(0, 0): 100.0, (1, 0): 0.2}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(registry: LambdaRegistry, formula: str):
    return evaluate(
        parse_formula(formula),
        lookup,
        registry.table(full_table),
    )


class TestDefinitionAndCall:
    def test_a_named_function_computes(self):
        reg = LambdaRegistry()
        reg.define("DISCOUNT", ["price", "rate"], "=price*(1-rate)")
        assert run(reg, "=DISCOUNT(100, 0.2)") == 80.0

    def test_it_reads_cells_through_its_arguments(self):
        reg = LambdaRegistry()
        reg.define("DISCOUNT", ["price", "rate"], "=price*(1-rate)")
        assert run(reg, "=DISCOUNT(A1, A2)") == 80.0

    def test_it_composes_with_builtins(self):
        reg = LambdaRegistry()
        reg.define("SQUARE", ["x"], "=x*x")
        assert run(reg, "=SUM(SQUARE(3), SQUARE(4))") == 25.0

    def test_a_lambda_can_call_another(self):
        reg = LambdaRegistry()
        reg.define("DOUBLE", ["x"], "=x*2")
        reg.define("QUAD", ["x"], "=DOUBLE(DOUBLE(x))")
        assert run(reg, "=QUAD(5)") == 20.0


class TestArgumentChecking:
    def test_too_few_arguments_are_refused(self):
        reg = LambdaRegistry()
        reg.define("ADD", ["a", "b"], "=a+b")
        outcome = run(reg, "=ADD(1)")
        assert outcome.code == "#VALUE!"
        assert "2 argument(s), got 1" in outcome.note

    def test_too_many_arguments_are_refused(self):
        reg = LambdaRegistry()
        reg.define("ADD", ["a", "b"], "=a+b")
        outcome = run(reg, "=ADD(1, 2, 3)")
        assert outcome.code == "#VALUE!"
        assert "got 3" in outcome.note

    def test_an_error_argument_carries_through(self):
        reg = LambdaRegistry()
        reg.define("ID", ["x"], "=x")
        outcome = run(reg, "=ID(1/0)")
        assert outcome.code == "#DIV/0!"


class TestRefusals:
    def test_a_cell_like_parameter_is_refused(self):
        reg = LambdaRegistry()
        with pytest.raises(Invalid) as caught:
            reg.define("BAD", ["A1"], "=A1+1")
        assert "shadow the grid" in str(caught.value)

    def test_a_repeated_parameter_is_refused(self):
        reg = LambdaRegistry()
        with pytest.raises(Invalid) as caught:
            reg.define("BAD", ["x", "x"], "=x")
        assert "bind one name twice" in str(caught.value)

    def test_an_unknown_name_still_errors(self):
        reg = LambdaRegistry()
        outcome = run(reg, "=NOSUCH(1)")
        assert outcome.code == "#NAME?"
