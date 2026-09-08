"""Pivot tables: group, aggregate, and answer the average-of-averages question.

A pivot table is a group-by dressed for the grid: a source
region whose first row names the fields, a spec naming which
field labels the rows, which labels the columns, and which
gets aggregated, and a report that lays the buckets out with
totals on both edges. Two decisions here are the kind that
silently diverge between implementations, so they are made
loudly. First, the grand total aggregates the records, not
the bucket results: the grand AVERAGE is the mean of every
matching value, not the mean of the row means, because the
mean of means weights a two-record bucket the same as a
two-hundred-record bucket and that lie has misread a
thousand quarterly reviews. Second, errors poison exactly
the buckets that contain them: a #DIV/0! in one region's
sales wrecks that cell, its row total, its column total, and
the grand total, and leaves every other bucket standing,
which follows the value model's oath that errors flow but do
not explode. Construction problems are different in kind
from data problems and are treated differently: a field name
missing from the header row, a duplicate header, or an
unknown aggregation raises at build time, because those are
the author's typos, not the data's condition.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import Value, is_error, render

AGGREGATIONS = ("SUM", "COUNT", "AVERAGE", "MIN", "MAX")


@dataclass(frozen=True)
class PivotSpec:
    rows: str
    values: str
    agg: str = "SUM"
    columns: str | None = None


@dataclass
class PivotReport:
    row_labels: list[str]
    col_labels: list[str]
    cells: dict[tuple[str, str], Value]
    row_totals: dict[str, Value]
    col_totals: dict[str, Value]
    grand: Value


def _aggregate(agg: str, values: list[Value]) -> Value:
    for value in values:
        if is_error(value):
            return value
    numbers = [
        v
        for v in values
        if isinstance(v, float) and not isinstance(v, bool)
    ]
    if agg == "COUNT":
        return float(len(numbers))
    if not numbers:
        return None
    if agg == "SUM":
        return sum(numbers)
    if agg == "AVERAGE":
        return sum(numbers) / len(numbers)
    if agg == "MIN":
        return min(numbers)
    return max(numbers)


@dataclass
class PivotTable:
    sheet: Sheet
    region: RangeRef
    spec: PivotSpec

    def _headers(self) -> dict[str, int]:
        headers: dict[str, int] = {}
        for col in range(self.region.left, self.region.right + 1):
            label = self.sheet.value_of(
                CellRef(row=self.region.top, col=col)
            )
            if not isinstance(label, str) or not label.strip():
                raise Invalid(
                    "every column in the source needs a text "
                    f"header; column {col + 1} has "
                    f"{render(label) if label is not None else 'nothing'}"
                )
            key = label.strip().upper()
            if key in headers:
                raise Invalid(
                    f"the header {label!r} appears twice; a "
                    "pivot cannot aggregate an ambiguous field"
                )
            headers[key] = col
        return headers

    def _column_for(
        self, headers: dict[str, int], field: str
    ) -> int:
        key = field.strip().upper()
        if key not in headers:
            available = ", ".join(sorted(headers))
            raise Invalid(
                f"no field named {field!r}; the source has "
                f"{available}"
            )
        return headers[key]

    def build(self) -> PivotReport:
        if self.spec.agg not in AGGREGATIONS:
            options = ", ".join(AGGREGATIONS)
            raise Invalid(
                f"unknown aggregation {self.spec.agg!r}; "
                f"pick one of {options}"
            )
        headers = self._headers()
        row_col = self._column_for(headers, self.spec.rows)
        value_col = self._column_for(headers, self.spec.values)
        col_col = (
            self._column_for(headers, self.spec.columns)
            if self.spec.columns is not None
            else None
        )
        buckets: dict[tuple[str, str], list[Value]] = {}
        by_row: dict[str, list[Value]] = {}
        by_col: dict[str, list[Value]] = {}
        everything: list[Value] = []
        for row in range(
            self.region.top + 1, self.region.bottom + 1
        ):
            row_label = self.sheet.value_of(
                CellRef(row=row, col=row_col)
            )
            if row_label is None:
                continue
            row_key = render(row_label)
            if col_col is None:
                col_key = self.spec.values.strip().upper()
            else:
                col_value = self.sheet.value_of(
                    CellRef(row=row, col=col_col)
                )
                col_key = (
                    render(col_value)
                    if col_value is not None
                    else "(blank)"
                )
            value = self.sheet.value_of(
                CellRef(row=row, col=value_col)
            )
            buckets.setdefault((row_key, col_key), []).append(
                value
            )
            by_row.setdefault(row_key, []).append(value)
            by_col.setdefault(col_key, []).append(value)
            everything.append(value)
        agg = self.spec.agg
        return PivotReport(
            row_labels=sorted(by_row),
            col_labels=sorted(by_col),
            cells={
                key: _aggregate(agg, values)
                for key, values in buckets.items()
            },
            row_totals={
                key: _aggregate(agg, values)
                for key, values in by_row.items()
            },
            col_totals={
                key: _aggregate(agg, values)
                for key, values in by_col.items()
            },
            grand=_aggregate(agg, everything),
        )

    def render(self) -> str:
        report = self.build()
        headings = [
            self.spec.rows.strip().upper(),
            *report.col_labels,
            "TOTAL",
        ]
        rows: list[list[str]] = [headings]
        for row_key in report.row_labels:
            line = [row_key]
            for col_key in report.col_labels:
                value = report.cells.get((row_key, col_key))
                line.append(
                    render(value) if value is not None else ""
                )
            total = report.row_totals[row_key]
            line.append(
                render(total) if total is not None else ""
            )
            rows.append(line)
        grand_line = ["TOTAL"]
        for col_key in report.col_labels:
            total = report.col_totals[col_key]
            grand_line.append(
                render(total) if total is not None else ""
            )
        grand_line.append(
            render(report.grand)
            if report.grand is not None
            else ""
        )
        rows.append(grand_line)
        widths = [
            max(len(line[index]) for line in rows)
            for index in range(len(headings))
        ]
        formatted = []
        for line in rows:
            cells = [line[0].ljust(widths[0])]
            cells.extend(
                text.rjust(widths[index])
                for index, text in enumerate(line[1:], 1)
            )
            formatted.append("  ".join(cells).rstrip())
        return "\n".join(formatted)
