"""Slicers: click-to-include filters that show what they are hiding.

A slicer is a filter with a conscience: instead of a typed
criterion, it offers the distinct values in a column as
buttons, and the view shows the rows whose value is among the
selected buttons. Its whole reason to exist over a plain
filter is visibility, so the model always answers two
questions a hidden filter cannot: which values are currently
included, and which exist but are switched off, because a
report filtered by an invisible rule is a report the reader
cannot trust. The default is everything selected, the honest
identity, so a freshly built slicer hides nothing until a
choice is made. Selecting down to no values is legal and
distinct from selecting everything, because show-me-nothing
is a real, if unusual, request and collapsing it to show-me-
everything would be the surprise that hides an empty result
behind a full one. A value that does not appear in the column
cannot be selected, refused by name rather than stored as a
button that matches nothing, because a phantom selection is a
filter the user thinks is doing something and is not. The
distinct values are read from the live column each time they
are listed, so a slicer built before data changed reflects
the data as it is, not a snapshot of what it was.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import Value, render


def _shown(value: Value) -> str:
    if isinstance(value, str):
        return value
    return render(value)


@dataclass
class Slicer:
    sheet: Sheet
    region: RangeRef
    column: int
    excluded: set[str] = field(default_factory=set)

    def available(self) -> list[str]:
        seen = []
        for row in range(
            self.region.top, self.region.bottom + 1
        ):
            value = self.sheet.value_of(
                CellRef(row=row, col=self.column)
            )
            if value is None:
                continue
            label = _shown(value)
            if label not in seen:
                seen.append(label)
        return seen

    def selected(self) -> list[str]:
        return [
            v
            for v in self.available()
            if v not in self.excluded
        ]

    def switched_off(self) -> list[str]:
        return [
            v
            for v in self.available()
            if v in self.excluded
        ]

    def toggle_off(self, label: str) -> str:
        if label not in self.available():
            raise Invalid(
                f"{label!r} is not a value in this column; "
                "a phantom selection filters nothing"
            )
        self.excluded.add(label)
        return f"{label!r} switched off"

    def toggle_on(self, label: str) -> str:
        self.excluded.discard(label)
        return f"{label!r} switched on"

    def visible_rows(self) -> list[int]:
        rows = [self.region.top]
        for row in range(
            self.region.top + 1, self.region.bottom + 1
        ):
            value = self.sheet.value_of(
                CellRef(row=row, col=self.column)
            )
            label = (
                _shown(value)
                if value is not None
                else None
            )
            if label is not None and (
                label not in self.excluded
            ):
                rows.append(row)
        return rows

    def state(self) -> str:
        on = self.selected()
        off = self.switched_off()
        return (
            f"showing {on}; hiding {off}"
            if off
            else f"showing all {len(on)} value(s)"
        )
