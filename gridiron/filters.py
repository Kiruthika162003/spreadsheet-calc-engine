"""Autofilter: a view that hides rows without ever moving them.

A filter is a pair of glasses, not a surgery: the rows stay
where they are, the view reports which are visible, and
removing the filter restores everything because nothing was
ever gone. Criteria stack per column with AND semantics
across columns, matching what every user expects from the
dropdown, and the header row is exempt by construction
since a filter that hides its own headers has blinded its
next user. The visible-summary functions exist because
aggregates over filtered data are the classic silent error:
SUM sums hidden rows too, and the report says so, offering
the visible subtotal beside the full total so the
difference is a number on the page instead of a surprise
in a meeting.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.criteria import Criterion
from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet


@dataclass
class FilterView:
    sheet: Sheet
    region: RangeRef
    column_criteria: dict[int, Criterion] = field(
        default_factory=dict
    )

    def add_criterion(
        self, column: int, criterion_text: str
    ) -> None:
        if not (
            self.region.left <= column <= self.region.right
        ):
            raise Invalid(
                f"column {column} is outside the filtered "
                f"region {self.region.a1()}"
            )
        self.column_criteria[column] = Criterion.parse(
            criterion_text
        )

    def clear_criteria(self) -> str:
        count = len(self.column_criteria)
        self.column_criteria.clear()
        return (
            f"{count} criterion(s) removed; every row "
            "returns because nothing was ever gone"
        )

    def visible_rows(self) -> list[int]:
        visible = [self.region.top]
        for row in range(
            self.region.top + 1, self.region.bottom + 1
        ):
            keep = True
            for column, criterion in (
                self.column_criteria.items()
            ):
                value = self.sheet.value_of(
                    CellRef(row=row, col=column)
                )
                if not criterion.matches(value):
                    keep = False
                    break
            if keep:
                visible.append(row)
        return visible

    def hidden_count(self) -> int:
        total_rows = self.region.bottom - self.region.top + 1
        return total_rows - len(self.visible_rows())

    def visible_sum(self, column: int) -> str:
        visible = set(self.visible_rows()) - {
            self.region.top
        }
        full_total = 0.0
        visible_total = 0.0
        for row in range(
            self.region.top + 1, self.region.bottom + 1
        ):
            value = self.sheet.value_of(
                CellRef(row=row, col=column)
            )
            if isinstance(value, float) and not isinstance(
                value, bool
            ):
                full_total += value
                if row in visible:
                    visible_total += value
        return (
            f"visible {visible_total} of {full_total} "
            "total; SUM sums hidden rows too, and the "
            "difference belongs on the page, not in a "
            "meeting"
        )
