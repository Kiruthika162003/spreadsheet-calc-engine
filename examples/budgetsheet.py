"""A budget sheet: imports, conditions, lookups, and the audit trail.

Run with: python -m examples.budgetsheet
"""

from __future__ import annotations

from gridiron.csvio import import_csv
from gridiron.engine import Engine
from gridiron.refs import CellRef
from gridiron.tracer import Tracer
from gridiron.values import render

EXPENSES = (
    "category,amount\n"
    "rent,1200\n"
    "food,450\n"
    "transit,120\n"
    "food,180\n"
    "rent,80\n"
)


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def main() -> int:
    engine = Engine()
    report = import_csv(engine.sheet, EXPENSES)
    print(f"import:  {report.line().split(';')[0]}")

    engine.set_formula(ref("D1"), "=SUM(B2:B6)")
    engine.set_formula(
        ref("D2"), '=SUMIF(A2:A6, "rent", B2:B6)'
    )
    engine.set_formula(
        ref("D3"), '=COUNTIF(A2:A6, "food")'
    )
    engine.set_formula(
        ref("D4"),
        '=IF(D2/D1>0.5, "rent heavy", "balanced")',
    )
    engine.full_recalc()

    print(f"total:   {render(engine.value(ref('D1')))}")
    print(f"rent:    {render(engine.value(ref('D2')))}")
    print(f"food:    {render(engine.value(ref('D3')))} line items")
    print(f"verdict: {render(engine.value(ref('D4')))}")

    tracer = Tracer(engine=engine)
    print(f"audit:   {tracer.dependents(ref('B2'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
