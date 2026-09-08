"""Merged cells: one value wearing a larger rectangle, with the rules stated.

Merging is a display decision that keeps leaking into
semantics, so this module writes the leak's rules down: the
top-left cell is the region's only real cell, the covered
cells must be empty at merge time because merging over data
silently deletes it in the incumbent and silent deletion is
against this house's religion, and any attempt to write into
a covered cell is redirected as a refusal naming the anchor.
Ranges that partially overlap a merge are the poison case,
a SUM half inside a merged region counts the anchor once and
the shadows as empty, which is the incumbent's rule and the
least bad one available, stated here so nobody discovers it
during an audit. Unmerging releases the rectangle and the
value stays with the anchor, where it always really lived.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet


@dataclass
class MergeRegistry:
    sheet: Sheet
    regions: list[RangeRef] = field(default_factory=list)

    def merge(self, region: RangeRef) -> str:
        if region.size() < 2:
            raise Invalid(
                "a one-cell merge is a cell wearing a costume"
            )
        for existing in self.regions:
            for cell in region.cells():
                if existing.contains(cell):
                    raise Invalid(
                        f"{region.a1()} overlaps the merge "
                        f"at {existing.a1()}; merges do not "
                        "stack"
                    )
        anchor = CellRef(row=region.top, col=region.left)
        for cell in region.cells():
            if cell.key() == anchor.key():
                continue
            if self.sheet.cell(cell) is not None:
                raise Invalid(
                    f"{cell.a1()} holds data; merging over "
                    "it would silently delete, which is "
                    "against this house's religion"
                )
        self.regions.append(region)
        return (
            f"{region.a1()} merged; {anchor.a1()} is the "
            "only real cell inside"
        )

    def anchor_of(self, ref: CellRef) -> CellRef | None:
        for region in self.regions:
            if region.contains(ref):
                return CellRef(
                    row=region.top, col=region.left
                )
        return None

    def check_write(self, ref: CellRef) -> None:
        anchor = self.anchor_of(ref)
        if anchor is not None and anchor.key() != ref.key():
            raise Invalid(
                f"{ref.a1()} is covered by the merge "
                f"anchored at {anchor.a1()}; write there "
                "instead, where the value really lives"
            )

    def unmerge(self, region: RangeRef) -> str:
        for index, existing in enumerate(self.regions):
            if existing == region:
                self.regions.pop(index)
                anchor = CellRef(
                    row=region.top, col=region.left
                )
                return (
                    f"{region.a1()} released; the value "
                    f"stays with {anchor.a1()}, where it "
                    "always really lived"
                )
        raise Invalid(f"{region.a1()} is not a merge")

    def census(self) -> str:
        if not self.regions:
            return "no merges; every rectangle is one cell wide"
        lines = [f"{len(self.regions)} merge(s):"]
        for region in self.regions:
            lines.append(
                f"  {region.a1()} anchored at "
                f"{CellRef(row=region.top, col=region.left).a1()}"
            )
        return "\n".join(lines)
