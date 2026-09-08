"""Deduplication: keep the first sighting, report every row it displaced.

Removing duplicate rows is a destructive operation dressed as
a tidy one, so this module makes the destruction auditable:
it keeps the first occurrence of each key and returns a
report naming every row it dropped and which surviving row
each duplicate matched, because a dedup that silently
deletes forty rows is indistinguishable from a bug that ate
them. The key is one or more columns, and a row's identity
is the tuple of its key cells compared with the engine's own
type rules, so the number 5 and the text "5" are different
keys, matching how the rest of the grid already refuses to
conflate them. Empty key cells are part of the key, not
wildcards, because two rows blank in the same column are
genuinely the same key and treating blank as "matches
anything" is how a dedup collapses a table to one row.
Case folding is offered but off by default and stated when
on, since whether "Ada" and "ADA" are the same customer is
a business decision the function must not make silently. The
operation never touches formula cells in the key columns; it
refuses, because a key computed by a formula changes when
the sheet does and a dedup keyed on a moving target is a
snapshot lying about being a rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import Value, render


@dataclass
class DedupReport:
    kept: int = 0
    dropped: list[tuple[str, str]] = field(
        default_factory=list
    )

    def line(self) -> str:
        return (
            f"{self.kept} row(s) kept, "
            f"{len(self.dropped)} duplicate(s) removed"
        )

    def full(self) -> str:
        lines = [
            f"row {dup} duplicated {survivor}"
            for dup, survivor in self.dropped
        ]
        lines.append(self.line())
        return "\n".join(lines)


def _key_of(
    sheet: Sheet,
    row: int,
    key_cols: tuple[int, ...],
    fold_case: bool,
) -> tuple:
    parts = []
    for col in key_cols:
        value = sheet.value_of(CellRef(row=row, col=col))
        if fold_case and isinstance(value, str):
            value = value.upper()
        parts.append(_hashable(value))
    return tuple(parts)


def _hashable(value: Value):
    if value is None:
        return ("blank",)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, float):
        return ("number", value)
    return ("text", value)


@dataclass
class Deduplicator:
    sheet: Sheet

    def dedup(
        self,
        region: RangeRef,
        key_cols: tuple[int, ...],
        fold_case: bool = False,
    ) -> DedupReport:
        for col in key_cols:
            if not region.left <= col <= region.right:
                raise Invalid(
                    f"key column {col} is outside "
                    f"{region.a1()}"
                )
        for row in range(region.top, region.bottom + 1):
            for col in key_cols:
                cell = self.sheet.cell(
                    CellRef(row=row, col=col)
                )
                if cell is not None and cell.is_formula():
                    raise Invalid(
                        f"{CellRef(row=row, col=col).a1()} "
                        "is a formula key; a dedup keyed on "
                        "a moving target is a snapshot lying "
                        "about being a rule"
                    )
        seen: dict[tuple, int] = {}
        survivors: list[list[Value]] = []
        report = DedupReport()
        for row in range(region.top, region.bottom + 1):
            key = _key_of(
                self.sheet, row, key_cols, fold_case
            )
            if key in seen:
                report.dropped.append(
                    (
                        str(row + 1),
                        f"row {seen[key] + 1}",
                    )
                )
                continue
            seen[key] = row
            survivors.append(
                [
                    self.sheet.value_of(
                        CellRef(row=row, col=col)
                    )
                    for col in range(
                        region.left, region.right + 1
                    )
                ]
            )
        report.kept = len(survivors)
        self._rewrite(region, survivors)
        return report

    def _rewrite(
        self, region: RangeRef, survivors: list[list[Value]]
    ) -> None:
        for row in range(region.top, region.bottom + 1):
            for col in range(
                region.left, region.right + 1
            ):
                self.sheet.cells.pop(
                    CellRef(row=row, col=col).key(), None
                )
        for offset, values in enumerate(survivors):
            for col_offset, value in enumerate(values):
                if value is None:
                    continue
                self.sheet.set_literal(
                    CellRef(
                        row=region.top + offset,
                        col=region.left + col_offset,
                    ),
                    value,
                )


def render_key(parts: tuple) -> str:
    shown = []
    for part in parts:
        if part == ("blank",):
            shown.append("(blank)")
        else:
            shown.append(render(part[1]))
    return " | ".join(shown)
