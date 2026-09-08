from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.higherorder import HigherOrder
from gridiron.lambdas import LambdaRegistry
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.spill import SpillManager
from gridiron.values import is_error


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def setup(values: list[float]) -> HigherOrder:
    sheet = Sheet()
    for row, value in enumerate(values):
        sheet.set_literal(CellRef(row=row, col=0), value)
    registry = LambdaRegistry()
    return HigherOrder(
        sheet=sheet,
        spill=SpillManager(sheet=sheet),
        registry=registry,
    )


class TestMap:
    def test_it_squares_a_column(self):
        ho = setup([1.0, 2.0, 3.0])
        ho.registry.define("SQ", ["x"], "=x*x")
        verdict = ho.map_region(
            RangeRef.parse("A1:A3"), "SQ", ref("C1")
        )
        assert "spilled" in verdict
        assert ho.sheet.value_of(ref("C1")) == 1.0
        assert ho.sheet.value_of(ref("C2")) == 4.0
        assert ho.sheet.value_of(ref("C3")) == 9.0

    def test_an_unknown_function_is_refused(self):
        ho = setup([1.0])
        with pytest.raises(Invalid) as caught:
            ho.map_region(
                RangeRef.parse("A1:A1"), "GHOST", ref("C1")
            )
        assert "no function named" in str(caught.value)


class TestReduce:
    def test_it_sums_from_zero(self):
        ho = setup([1.0, 2.0, 3.0, 4.0])
        ho.registry.define(
            "ADD", ["acc", "x"], "=acc+x"
        )
        result = ho.reduce_region(
            RangeRef.parse("A1:A4"), 0.0, "ADD"
        )
        assert result == 10.0

    def test_the_initial_matters_for_products(self):
        ho = setup([2.0, 3.0, 4.0])
        ho.registry.define(
            "MUL", ["acc", "x"], "=acc*x"
        )
        # Product needs identity 1, not 0.
        assert (
            ho.reduce_region(
                RangeRef.parse("A1:A3"), 1.0, "MUL"
            )
            == 24.0
        )
        assert (
            ho.reduce_region(
                RangeRef.parse("A1:A3"), 0.0, "MUL"
            )
            == 0.0
        )

    def test_an_error_stops_the_fold(self):
        ho = setup([2.0, 0.0, 5.0])
        ho.registry.define(
            "DIV", ["acc", "x"], "=acc/x"
        )
        result = ho.reduce_region(
            RangeRef.parse("A1:A3"), 100.0, "DIV"
        )
        assert is_error(result)
        assert result.code == "#DIV/0!"

    def test_a_wrong_arity_lambda_is_refused_by_the_call(self):
        ho = setup([1.0, 2.0])
        ho.registry.define("ONE", ["x"], "=x*2")
        result = ho.reduce_region(
            RangeRef.parse("A1:A2"), 0.0, "ONE"
        )
        assert is_error(result)
        assert result.code == "#VALUE!"
