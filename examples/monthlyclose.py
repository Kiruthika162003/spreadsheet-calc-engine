"""A monthly close: three month sheets, one year-to-date gathered across them.

Run with: python -m examples.monthlyclose
"""

from __future__ import annotations

from gridiron.crosssheet3d import average3d, count3d, sum3d
from gridiron.refs import CellRef
from gridiron.values import render
from gridiron.workbook import Workbook


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


MONTHS = ["Jan", "Feb", "Mar"]


def build_book() -> Workbook:
    book = Workbook()
    revenues = {"Jan": 1200.0, "Feb": 1500.0, "Mar": 1800.0}
    for month in MONTHS:
        sheet = book.add_sheet(month)
        sheet.set_literal(ref("B1"), revenues[month])
    return book


def main() -> int:
    book = build_book()
    print(
        f"ytd:     {render(sum3d(book, MONTHS, ref('B1')))}"
    )
    print(
        "average: "
        f"{render(average3d(book, MONTHS, ref('B1')))}"
    )
    print(
        f"months:  {render(count3d(book, MONTHS, ref('B1')))}"
    )

    print(book.drop_sheet("Feb").split(";")[0])
    wounded = sum3d(book, MONTHS, ref("B1"))
    print(f"wound:   YTD now reads {wounded.code}")

    survivors = ["Jan", "Mar"]
    print(
        "reclose: "
        f"{render(sum3d(book, survivors, ref('B1')))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
