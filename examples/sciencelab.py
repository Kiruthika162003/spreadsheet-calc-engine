"""A science lab: measurements, a histogram spilled, a sparkline stated.

Run with: python -m examples.sciencelab
"""

from __future__ import annotations

from gridiron.arrays import ArrayLab
from gridiron.charts import Series, sparkline
from gridiron.engine import Engine
from gridiron.refs import CellRef, RangeRef
from gridiron.spill import SpillManager
from gridiron.values import render

READINGS = (
    4.8,
    5.1,
    4.9,
    5.6,
    5.0,
    4.7,
    5.2,
    6.1,
    5.0,
    4.9,
)


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def build_lab() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), "Reading")
    for index, reading in enumerate(READINGS):
        engine.set_literal(
            CellRef(row=index + 1, col=0), reading
        )
    engine.set_formula(
        ref("C1"), "=ROUND(AVERAGE(A2:A11), 3)"
    )
    engine.set_formula(ref("C2"), "=MEDIAN(A2:A11)")
    engine.set_formula(
        ref("C3"), "=ROUND(STDEV(A2:A11), 4)"
    )
    engine.set_formula(
        ref("C4"), "=ROUND(PERCENTILE(A2:A11, 0.9), 3)"
    )
    return engine


def main() -> int:
    engine = build_lab()
    print(f"mean:    {render(engine.value(ref('C1')))}")
    print(f"median:  {render(engine.value(ref('C2')))}")
    print(f"stdev:   {render(engine.value(ref('C3')))}")
    print(f"p90:     {render(engine.value(ref('C4')))}")

    lab = ArrayLab(
        sheet=engine.sheet,
        spill=SpillManager(sheet=engine.sheet),
    )
    verdict = lab.frequency_region(
        RangeRef.parse("A2:A11"),
        [4.9, 5.1, 5.5],
        ref("E1"),
    )
    print(f"bins:    {verdict}")
    counts = [
        render(engine.value(CellRef(row=row, col=4)))
        for row in range(4)
    ]
    print(f"counts:  {' '.join(counts)}")

    series = Series.from_column(
        engine.sheet, RangeRef.parse("A1:A11")
    )
    print(f"trend:   {sparkline(series)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
