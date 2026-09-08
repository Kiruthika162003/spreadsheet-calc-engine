"""An editing session: manual calc, an undo, a snapshot, and a restore.

Run with: python -m examples.undosession
"""

from __future__ import annotations

from gridiron.calcmodes import CalcController
from gridiron.engine import Engine
from gridiron.refs import CellRef
from gridiron.snapshots import SnapshotVault
from gridiron.undo import UndoStack


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def main() -> int:
    engine = Engine()
    engine.set_literal(ref("A1"), 100.0)
    engine.set_formula(ref("B1"), "=A1*1.2")
    engine.set_formula(ref("C1"), "=B1+A1")

    vault = SnapshotVault(sheet=engine.sheet)
    print(vault.take("baseline"))

    control = CalcController(engine=engine)
    print(control.set_manual())
    control.set_literal(ref("A1"), 200.0)
    print(f"pending: {control.pending_report()}")
    report = control.calculate()
    print(f"settled: C1 = {engine.value(ref('C1'))}")
    print(f"touched: {report.line()}")

    stack = UndoStack(engine=engine)
    stack.set_literal(ref("A1"), 999.0)
    print(f"typo:    C1 = {engine.value(ref('C1'))}")
    print(f"undo:    {stack.undo()}")
    print(f"back:    C1 = {engine.value(ref('C1'))}")

    print(vault.diff("baseline").line())
    print(vault.restore("baseline").split(";")[0])
    engine.full_recalc()
    print(f"restored: C1 = {engine.value(ref('C1'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
