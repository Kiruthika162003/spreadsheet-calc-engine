"""Dynamic spill: one formula, many cells, and the block that names its blocker.

SEQUENCE and its kin return regions from a single formula,
and the spill contract has two halves the incumbent taught
everyone: the anchor cell owns the formula while the spilled
cells are ghosts, readable but not editable, cleared the
moment the anchor changes; and a spill that would overwrite
an occupied cell does not partially land, it produces
#SPILL! at the anchor with the blocking cell named, because
a half-landed spill is corruption arranged in a rectangle.
Ghost cells know their anchor, editing one is refused with
the anchor's address so the user fixes the formula instead
of fighting its shadow, and clearing the anchor sweeps every
ghost, since orphaned ghosts are the other corruption, stale
values wearing a formula's authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.sheet import Sheet
from gridiron.values import ErrorValue, Value


@dataclass
class SpillManager:
    sheet: Sheet
    ghosts: dict[tuple[int, int], tuple[int, int]] = field(
        default_factory=dict
    )
    anchors: dict[
        tuple[int, int], list[tuple[int, int]]
    ] = field(default_factory=dict)

    def spill_sequence(
        self, anchor: CellRef, count: int, start: float = 1.0,
        step: float = 1.0,
    ) -> Value | str:
        if count < 1:
            raise Invalid("a sequence needs at least one term")
        targets = []
        for offset in range(count):
            target = CellRef(
                row=anchor.row + offset, col=anchor.col
            )
            if offset > 0 and (
                self.sheet.cell(target) is not None
            ):
                blocked = ErrorValue(
                    code="#VALUE!",
                    note=(
                        f"#SPILL! blocked by {target.a1()}; "
                        "a half-landed spill is corruption "
                        "arranged in a rectangle"
                    ),
                )
                self.sheet.set_literal(anchor, blocked)
                return blocked
            targets.append(target)
        values = [
            start + step * offset
            for offset in range(count)
        ]
        self.sheet.set_literal(anchor, values[0])
        ghost_keys = []
        for target, value in zip(
            targets[1:], values[1:], strict=True
        ):
            self.sheet.set_literal(target, value)
            self.ghosts[target.key()] = anchor.key()
            ghost_keys.append(target.key())
        self.anchors[anchor.key()] = ghost_keys
        return (
            f"{count} value(s) spilled from {anchor.a1()}"
        )

    def spill_grid(
        self, anchor: CellRef, grid: list[list[Value]]
    ) -> Value | str:
        if not grid or not grid[0]:
            raise Invalid("an empty grid cannot spill")
        widths = {len(row) for row in grid}
        if len(widths) != 1:
            raise Invalid(
                "a ragged grid cannot spill; every row must "
                "share a width"
            )
        targets: list[list[CellRef]] = []
        for row_offset, row in enumerate(grid):
            line = []
            for col_offset in range(len(row)):
                target = CellRef(
                    row=anchor.row + row_offset,
                    col=anchor.col + col_offset,
                )
                occupied = (
                    target.key() != anchor.key()
                    and self.sheet.cell(target) is not None
                )
                if occupied:
                    blocked = ErrorValue(
                        code="#VALUE!",
                        note=(
                            f"#SPILL! blocked by "
                            f"{target.a1()}; a half-landed "
                            "spill is corruption arranged "
                            "in a rectangle"
                        ),
                    )
                    self.sheet.set_literal(anchor, blocked)
                    return blocked
                line.append(target)
            targets.append(line)
        ghost_keys = []
        for row_targets, row_values in zip(
            targets, grid, strict=True
        ):
            for target, value in zip(
                row_targets, row_values, strict=True
            ):
                self.sheet.set_literal(target, value)
                if target.key() != anchor.key():
                    self.ghosts[target.key()] = anchor.key()
                    ghost_keys.append(target.key())
        self.anchors[anchor.key()] = ghost_keys
        return (
            f"{len(grid)}x{len(grid[0])} grid spilled from "
            f"{anchor.a1()}"
        )

    def edit_guard(self, ref: CellRef) -> None:
        owner = self.ghosts.get(ref.key())
        if owner is not None:
            anchor = CellRef(row=owner[0], col=owner[1])
            raise Invalid(
                f"{ref.a1()} is a spill ghost of "
                f"{anchor.a1()}; edit the anchor's formula "
                "instead of fighting its shadow"
            )

    def clear_anchor(self, anchor: CellRef) -> str:
        ghost_keys = self.anchors.pop(anchor.key(), None)
        if ghost_keys is None:
            raise Invalid(
                f"{anchor.a1()} anchors no spill"
            )
        self.sheet.clear(anchor)
        for key in ghost_keys:
            self.sheet.cells.pop(key, None)
            self.ghosts.pop(key, None)
        return (
            f"{anchor.a1()} cleared with "
            f"{len(ghost_keys)} ghost(s) swept; orphaned "
            "ghosts are stale values wearing a formula's "
            "authority"
        )
