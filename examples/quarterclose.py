"""Quarter close: dates, money, formats, and the scenario table.

Run with: python -m examples.quarterclose
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.numberformat import NumberFormat
from gridiron.refs import CellRef
from gridiron.scenarios import ScenarioManager
from gridiron.values import render


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def main() -> int:
    engine = Engine()
    engine.set_formula(ref("A1"), "=DATE(2024, 1, 1)")
    engine.set_formula(ref("A2"), "=DATE(2024, 3, 31)")
    engine.set_formula(
        ref("A3"), "=NETWORKDAYS(A1, A2)"
    )
    engine.full_recalc()
    print(
        f"workdays: {render(engine.value(ref('A3')))} in the quarter"
    )

    engine.set_literal(ref("B1"), 91250.0)
    engine.set_literal(ref("B2"), 0.19)
    engine.set_formula(ref("C1"), "=B1*(1-B2)")
    engine.full_recalc()
    money = NumberFormat.parse("#,##0.00")
    print(
        f"net:      {money.apply(engine.value(ref('C1')))}"
    )

    manager = ScenarioManager(engine=engine)
    manager.capture("filed", (ref("B1"), ref("B2")))
    engine.set_literal(ref("B1"), 98000.0)
    engine.set_literal(ref("B2"), 0.21)
    manager.capture("audited", (ref("B1"), ref("B2")))
    print(
        manager.summary(
            watched=(ref("C1"),),
            names=("filed", "audited"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
