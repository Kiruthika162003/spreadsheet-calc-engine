"""A workbook tour: three sheets, one edit, and the wound left on purpose.

Run with: python -m examples.workbooktour
"""

from __future__ import annotations

from gridiron.bookengine import BookEngine
from gridiron.refs import CellRef
from gridiron.values import render


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def build_book() -> BookEngine:
    engine = BookEngine()
    engine.add_sheet("Costs")
    engine.add_sheet("Revenue")
    engine.add_sheet("Summary")
    engine.set_literal("Costs", ref("A1"), 1200.0)
    engine.set_literal("Costs", ref("A2"), 640.0)
    engine.set_literal("Costs", ref("A3"), 380.0)
    engine.set_formula("Costs", ref("B1"), "=SUM(A1:A3)")
    engine.set_literal("Revenue", ref("A1"), 3100.0)
    engine.set_literal("Revenue", ref("A2"), 900.0)
    engine.set_formula("Revenue", ref("B1"), "=A1+A2")
    engine.set_formula(
        "Summary", ref("C1"), "=Revenue!B1-Costs!B1"
    )
    engine.set_formula("Summary", ref("C2"), "=C1/Revenue!B1")
    return engine


def main() -> int:
    engine = build_book()
    print(
        f"margin:  {render(engine.value('Summary', ref('C1')))}"
    )
    print(
        "share:   "
        f"{render(engine.value('Summary', ref('C2')))}"
    )

    verdict = engine.set_literal("Costs", ref("A2"), 940.0)
    print(f"edit:    {verdict}")
    print(
        f"margin:  {render(engine.value('Summary', ref('C1')))}"
    )

    print(engine.book.drop_sheet("Revenue"))
    engine.set_literal("Costs", ref("A3"), 400.0)
    wounded = engine.value("Summary", ref("C1"))
    print(f"wound:   C1 now reads {wounded.code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
