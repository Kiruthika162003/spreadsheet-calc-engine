"""A first sheet: a small ledger, one edit, and the proof the rest slept.

Run with: python -m examples.firstsheet
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.goalseek import GoalSeeker
from gridiron.refs import CellRef
from gridiron.values import render


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def build_ledger() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 120.0)
    engine.set_literal(ref("A2"), 85.0)
    engine.set_literal(ref("A3"), 43.0)
    engine.set_formula(ref("B1"), "=A1*1.19")
    engine.set_formula(ref("B2"), "=A2*1.19")
    engine.set_formula(ref("B3"), "=A3*1.19")
    engine.set_formula(ref("C1"), "=ROUND(SUM(B1:B3), 2)")
    engine.set_formula(ref("C2"), "=ROUND(AVERAGE(A1:A3), 1)")
    return engine


def main() -> int:
    engine = build_ledger()
    print(f"total:   {render(engine.value(ref('C1')))}")
    print(f"average: {render(engine.value(ref('C2')))}")

    report = engine.set_literal(ref("A2"), 100.0)
    print(
        f"edit:    A2 becomes 100; {report.line()}"
    )
    print(f"total:   {render(engine.value(ref('C1')))}")

    report = engine.set_formula(ref("D1"), '=LEFT("Quarter", 1)&1')
    print(f"label:   {render(engine.value(ref('D1')))}")

    verdict = GoalSeeker(engine=engine).seek(
        target_ref=ref("C1"),
        goal=350.0,
        input_ref=ref("A3"),
        low=0.0,
        high=200.0,
    )
    print(f"seek:    {verdict.split(' makes')[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
