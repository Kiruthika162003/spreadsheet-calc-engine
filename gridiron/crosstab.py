"""Cross-tabulation: counting records across two categories, with the margins.

A crosstab lays records out in a grid by two category fields,
region down the side and quarter across the top, and fills
each cell with a count or a sum of a value field. It is the
pure-data cousin of the sheet pivot, working on a list of
records rather than a region, and it holds the same honesty:
the row and column margins are the totals along each edge and
the grand total sits in the corner, and every margin is
derived from the cells so a margin that disagreed with its
row would betray a bug the grid is supposed to make
impossible. The aggregation is either counting records or
summing a numeric field, and summing a field that is missing
or non-numeric on some record is a decision, not a silent
skip: those records are tallied separately as excluded and
reported, because a sum that quietly dropped a third of the
rows is a wrong total nobody flagged. Row and column labels
come back sorted so the table reads predictably, but a caller
can read the raw cell map for the original insertion facts.
An empty record set produces an empty table with a zero grand
total rather than an error, because zero records is a real
and common state, the report before any data has arrived, and
refusing it would make every dashboard crash on its first
render.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CrossTab:
    cells: dict[tuple[str, str], float] = field(
        default_factory=dict
    )
    excluded: int = 0

    def rows(self) -> list[str]:
        return sorted({r for r, _ in self.cells})

    def columns(self) -> list[str]:
        return sorted({c for _, c in self.cells})

    def cell(self, row: str, column: str) -> float:
        return self.cells.get((row, column), 0.0)

    def row_total(self, row: str) -> float:
        return sum(
            v
            for (r, _), v in self.cells.items()
            if r == row
        )

    def column_total(self, column: str) -> float:
        return sum(
            v
            for (_, c), v in self.cells.items()
            if c == column
        )

    def grand_total(self) -> float:
        return sum(self.cells.values())


def _numeric(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(
        value, bool
    )


def crosstab_count(
    records: list[tuple[str, str]],
) -> CrossTab:
    table = CrossTab()
    for row, column in records:
        key = (row, column)
        table.cells[key] = table.cells.get(key, 0.0) + 1.0
    return table


def crosstab_sum(
    records: list[tuple[str, str, object]],
) -> CrossTab:
    table = CrossTab()
    for row, column, value in records:
        if not _numeric(value):
            table.excluded += 1
            continue
        key = (row, column)
        table.cells[key] = table.cells.get(key, 0.0) + value
    return table
