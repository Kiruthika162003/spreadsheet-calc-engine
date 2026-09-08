"""MAP and REDUCE: a function applied across a region, or folded into one value.

Once functions can be named, the natural next tools are the
ones that take a function as an argument. MAP applies a
one-parameter lambda to every cell of a region and lands the
results in the same shape through the spill manager, so
squaring a column or formatting a row is one call instead of
a copied formula down the side. REDUCE folds a two-parameter
lambda, accumulator and next value, across the region in
reading order starting from an explicit initial value, which
is the honest way to express a running total or a custom
aggregate the built-in family does not cover. The initial
value is required, not defaulted to zero, because the
identity of a fold depends on the operation, zero for a sum
but one for a product and negative infinity for a maximum,
and defaulting to zero would silently break every fold that
is not addition. An error produced by the lambda at any cell
stops the fold and becomes the result, and poisons the
mapped grid at that cell while the rest of MAP carries on,
matching how errors flow everywhere else. The lambda's arity
is checked by the lambda machinery itself, so MAP handed a
two-parameter function and REDUCE handed a one-parameter one
are refused with the count mismatch the call already knows
how to report, rather than a second parallel check that
could drift.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.ast import Bool, Node, Number, Text
from gridiron.errors import Invalid
from gridiron.lambdas import LambdaRegistry
from gridiron.library import full_table
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.spill import SpillManager
from gridiron.values import Value, is_error


def _as_node(value: Value) -> Node:
    if isinstance(value, bool):
        return Bool(value=value)
    if isinstance(value, float):
        return Number(value=value)
    if isinstance(value, str):
        return Text(value=value)
    return Text(value="")


@dataclass
class HigherOrder:
    sheet: Sheet
    spill: SpillManager
    registry: LambdaRegistry

    def _fn(self, name: str):
        table = self.registry.table(full_table)
        found = table(name)
        if found is None:
            raise Invalid(
                f"no function named {name!r} to apply"
            )
        return found, table

    def _call(self, fn, table, values: list[Value]) -> Value:
        args = tuple(_as_node(value) for value in values)
        return fn(
            args,
            self.sheet.value_of,
            table,
            lambda _name: None,
        )

    def map_region(
        self,
        source: RangeRef,
        lambda_name: str,
        anchor: CellRef,
    ) -> Value | str:
        fn, table = self._fn(lambda_name)
        grid: list[list[Value]] = []
        for row in range(source.top, source.bottom + 1):
            line = []
            for col in range(
                source.left, source.right + 1
            ):
                cell = self.sheet.value_of(
                    CellRef(row=row, col=col)
                )
                line.append(self._call(fn, table, [cell]))
            grid.append(line)
        return self.spill.spill_grid(anchor, grid)

    def reduce_region(
        self,
        source: RangeRef,
        initial: Value,
        lambda_name: str,
    ) -> Value:
        fn, table = self._fn(lambda_name)
        accumulator = initial
        for cell in source.cells():
            value = self.sheet.value_of(cell)
            accumulator = self._call(
                fn, table, [accumulator, value]
            )
            if is_error(accumulator):
                return accumulator
        return accumulator
