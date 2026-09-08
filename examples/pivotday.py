"""A pivot day: a table grows a row, a pivot summarizes it, an export ships it.

Run with: python -m examples.pivotday
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.exporters import Exporter
from gridiron.pivot import PivotSpec, PivotTable
from gridiron.refs import CellRef, RangeRef
from gridiron.tables import Table


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def build() -> Engine:
    engine = Engine()
    rows = (
        ("Region", "Quarter", "Sales"),
        ("East", "Q1", 100.0),
        ("West", "Q1", 200.0),
        ("East", "Q2", 150.0),
        ("West", "Q2", 50.0),
    )
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            engine.set_literal(CellRef(row=r, col=c), value)
    return engine


def main() -> int:
    engine = build()
    table = Table(
        name="Sales",
        sheet=engine.sheet,
        region=RangeRef.parse("A1:C5"),
    )
    print(table.add_row(
        {"Region": "East", "Quarter": "Q1", "Sales": 300.0}
    ))

    pivot = PivotTable(
        sheet=engine.sheet,
        region=table.region,
        spec=PivotSpec(
            rows="Region", columns="Quarter", values="Sales"
        ),
    )
    report = pivot.build()
    print(f"east Q1: {report.cells[('East', 'Q1')]}")
    print(f"grand:   {report.grand}")

    print("---")
    print(pivot.render())

    exporter = Exporter(
        sheet=engine.sheet,
        region=RangeRef.parse("A1:C6"),
    )
    markdown = exporter.to_markdown().splitlines()
    print("---")
    print(markdown[0])
    print(markdown[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
