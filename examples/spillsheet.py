"""A spill sheet: transpose, filter, and sort-by, each landing its rectangle.

Run with: python -m examples.spillsheet
"""

from __future__ import annotations

from gridiron.arrays import ArrayLab
from gridiron.dynarrays import DynamicArrays
from gridiron.engine import Engine
from gridiron.refs import CellRef, RangeRef
from gridiron.spill import SpillManager
from gridiron.values import render


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def build_sheet() -> Engine:
    engine = Engine()
    rows = (
        ("Ada", 88.0, True),
        ("Grace", 61.0, False),
        ("Alan", 95.0, True),
    )
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            engine.set_literal(CellRef(row=r, col=c), value)
    return engine


def main() -> int:
    engine = build_sheet()
    spill = SpillManager(sheet=engine.sheet)
    array = ArrayLab(sheet=engine.sheet, spill=spill)
    dynamic = DynamicArrays(
        sheet=engine.sheet, spill=spill
    )

    verdict = array.transpose_region(
        RangeRef.parse("A1:B3"), ref("E1")
    )
    print(f"transpose: {verdict}")
    print(
        "row1:      "
        + " ".join(
            render(engine.value(CellRef(row=0, col=c)))
            for c in range(4, 7)
        )
    )

    verdict = dynamic.filter(
        RangeRef.parse("A1:B3"),
        RangeRef.parse("C1:C3"),
        ref("E5"),
    )
    print(f"filter:    {verdict}")
    print(
        "kept:      "
        + ", ".join(
            render(engine.value(CellRef(row=r, col=4)))
            for r in (4, 5)
        )
    )

    verdict = dynamic.sortby(
        RangeRef.parse("A1:A3"),
        RangeRef.parse("B1:B3"),
        ref("G5"),
        descending=True,
    )
    print(f"sortby:    {verdict}")
    print(
        "ranked:    "
        + ", ".join(
            render(engine.value(CellRef(row=r, col=6)))
            for r in (4, 5, 6)
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
