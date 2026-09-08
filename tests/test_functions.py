from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.functions import builtin_table, register
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.values import ErrorValue

WORLD = {
    (0, 0): 10.0,
    (1, 0): 20.0,
    (2, 0): "12",
    (3, 0): True,
    (0, 2): ErrorValue(code="#REF!"),
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, builtin_table
    )


class TestTheFlattenRule:
    def test_referenced_text_is_ignored_and_typed_text_counts(self):
        assert run("=SUM(A1:A4)") == 30.0
        assert run('=SUM(A1, "12")').code == "#VALUE!"
        assert run("=SUM(A1, 12)") == 22.0

    def test_booleans_in_regions_do_not_count(self):
        assert run("=COUNT(A1:A4)") == 2.0

    def test_empty_cells_vanish_from_average_only(self):
        assert run("=SUM(A1:A9)") == 30.0
        assert run("=AVERAGE(A1:A2)") == 15.0

    def test_errors_poison_every_aggregate(self):
        assert run("=SUM(A1, C1)").code == "#REF!"
        assert run("=MAX(C1:C2)").code == "#REF!"


class TestAggregates:
    def test_min_max_and_the_empty_refusal(self):
        assert run("=MIN(A1:A2)") == 10.0
        assert run("=MAX(A1:A2)") == 20.0
        empty = run("=AVERAGE(F1:F3)")
        assert empty.code == "#DIV/0!"
        assert "has no answer" in empty.note


class TestIf:
    def test_the_untaken_branch_is_allowed_to_be_broken(self):
        assert run("=IF(A1>5, 1, 1/0)") == 1.0
        assert run("=IF(A1<5, 1/0, 2)") == 2.0

    def test_the_condition_itself_can_poison(self):
        assert run("=IF(C1, 1, 2)").code == "#REF!"

    def test_the_two_arg_form_defaults_to_false(self):
        assert run("=IF(A1<5, 1)") is False

    def test_the_wrong_arity_names_the_shape(self):
        assert run("=IF(A1)").code == "#VALUE!"


class TestScalars:
    def test_round_and_abs(self):
        assert run("=ROUND(2.567, 2)") == 2.57
        assert run("=ROUND(2.5)") == 2.0
        assert run("=ABS(0-9)") == 9.0


class TestRegistration:
    def test_shadowing_a_builtin_is_refused(self):
        with pytest.raises(Invalid) as caught:
            register("sum", lambda *_: 0.0)
        assert "never heard of you" in str(caught.value)
