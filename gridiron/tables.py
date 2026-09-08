"""Structured tables: columns with names, and names that follow the table.

A table is a region that promised to behave: a header row of
unique text names, a body that grows downward, and columns
addressable by what they are called instead of where they
sit. The incumbent's bracket syntax does not fit this
grammar's lexer, so the bridge is the dot form the lexer
already speaks: a table named ORDERS with a column AMOUNT
binds the defined name ORDERS.AMOUNT, and any formula can
say SUM(ORDERS.AMOUNT) through the ordinary name table. The
binding resolves at evaluation time against the table's
live region, not a snapshot taken at bind time, so adding a
row grows every formula that speaks the name, which is the
entire reason users reach for tables over ranges: the range
that forgets to grow is the oldest quarterly-report bug in
the book. Rows are added by column name and refuse unknown
names with the header row quoted, totals fold each column
under its own chosen aggregation with errors poisoning only
the columns that contain them, and two tables cannot share
a name, since a registry that shrugs at collisions is a
name table that lies.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.ast import Node, Range
from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import Value, is_error


@dataclass
class Table:
    name: str
    sheet: Sheet
    region: RangeRef

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise Invalid("a table needs a name")
        if self.region.bottom == self.region.top:
            raise Invalid(
                f"table {self.name} has a header row and no "
                "body; a table of nothing is a range with "
                "ambitions"
            )
        self._validate_headers()

    def _validate_headers(self) -> None:
        seen = set()
        for col in range(self.region.left, self.region.right + 1):
            label = self.sheet.value_of(
                CellRef(row=self.region.top, col=col)
            )
            if not isinstance(label, str) or not label.strip():
                raise Invalid(
                    f"table {self.name} needs text headers; "
                    f"column {col + 1} lacks one"
                )
            key = label.strip().upper()
            if key in seen:
                raise Invalid(
                    f"table {self.name} repeats the header "
                    f"{label!r}; columns need distinct names"
                )
            seen.add(key)

    def columns(self) -> list[str]:
        return [
            str(
                self.sheet.value_of(
                    CellRef(row=self.region.top, col=col)
                )
            ).strip().upper()
            for col in range(
                self.region.left, self.region.right + 1
            )
        ]

    def _column_index(self, column: str) -> int:
        names = self.columns()
        key = column.strip().upper()
        if key not in names:
            row = ", ".join(names)
            raise Invalid(
                f"table {self.name} has no column "
                f"{column!r}; the header row reads {row}"
            )
        return self.region.left + names.index(key)

    def body_range(self, column: str) -> RangeRef:
        col = self._column_index(column)
        return RangeRef(
            top=self.region.top + 1,
            left=col,
            bottom=self.region.bottom,
            right=col,
        )

    def column_values(self, column: str) -> list[Value]:
        body = self.body_range(column)
        return [
            self.sheet.value_of(cell)
            for cell in body.cells()
        ]

    def add_row(self, values: dict[str, Value]) -> str:
        names = self.columns()
        for key in values:
            if key.strip().upper() not in names:
                row = ", ".join(names)
                raise Invalid(
                    f"table {self.name} has no column "
                    f"{key!r}; the header row reads {row}"
                )
        new_row = self.region.bottom + 1
        for column, value in values.items():
            self.sheet.set_literal(
                CellRef(
                    row=new_row,
                    col=self._column_index(column),
                ),
                value,
            )
        self.region = RangeRef(
            top=self.region.top,
            left=self.region.left,
            bottom=new_row,
            right=self.region.right,
        )
        filled = len(values)
        width = len(names)
        return (
            f"{self.name} grew to row {new_row + 1}; "
            f"{filled} of {width} column(s) filled"
        )

    def totals(
        self, aggregations: dict[str, str]
    ) -> dict[str, Value]:
        folds = {
            "SUM": sum,
            "MIN": min,
            "MAX": max,
        }
        results: dict[str, Value] = {}
        for column, agg in aggregations.items():
            key = agg.strip().upper()
            if key not in (*folds, "COUNT", "AVERAGE"):
                raise Invalid(
                    f"unknown aggregation {agg!r} for "
                    f"{column}; pick SUM, COUNT, AVERAGE, "
                    "MIN, or MAX"
                )
            values = self.column_values(column)
            poisoned = next(
                (v for v in values if is_error(v)), None
            )
            if poisoned is not None:
                results[column.strip().upper()] = poisoned
                continue
            numbers = [
                v
                for v in values
                if isinstance(v, float)
                and not isinstance(v, bool)
            ]
            if key == "COUNT":
                results[column.strip().upper()] = float(
                    len(numbers)
                )
            elif not numbers:
                results[column.strip().upper()] = None
            elif key == "AVERAGE":
                results[column.strip().upper()] = sum(
                    numbers
                ) / len(numbers)
            else:
                results[column.strip().upper()] = folds[key](
                    numbers
                )
        return results


@dataclass
class TableRegistry:
    tables: dict[str, Table] = field(default_factory=dict)

    def add(self, table: Table) -> str:
        key = table.name.strip().upper()
        if key in self.tables:
            raise Invalid(
                f"a table named {table.name} already "
                "exists; a registry that shrugs at "
                "collisions is a name table that lies"
            )
        self.tables[key] = table
        bound = len(table.columns())
        return (
            f"{table.name} registered with {bound} "
            "column name(s)"
        )

    def resolve(self, name: str) -> Node | None:
        table_part, dot, column_part = name.partition(".")
        if not dot:
            return None
        table = self.tables.get(table_part.strip().upper())
        if table is None:
            return None
        try:
            body = table.body_range(column_part)
        except Invalid:
            return None
        return Range(ref=body)
