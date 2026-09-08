"""An audit day: a wounded model, and the three tools that find the wound.

Run with: python -m examples.auditday
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.errorhints import ErrorDoctor
from gridiron.inspector import Inspector
from gridiron.refs import CellRef
from gridiron.tracer import Tracer


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def build_model() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 1000.0)
    engine.set_literal(ref("A2"), 0.0)
    engine.set_formula(ref("B1"), "=A1*1.1")
    engine.set_formula(ref("B2"), "=B1/A2")
    engine.set_formula(ref("C1"), "=B1+B2")
    engine.set_formula(ref("D1"), "=C1*2")
    return engine


def main() -> int:
    engine = build_model()
    doctor = ErrorDoctor(engine=engine)
    print(f"census:  {doctor.census().splitlines()[0]}")
    diagnosis = doctor.diagnose(ref("D1"))
    print(f"origin:  {diagnosis.origin.a1()}")
    print(f"trail:   {' <- '.join(diagnosis.path)}")

    tracer = Tracer(engine=engine)
    wall = Inspector(engine=engine).load_bearing_wall()
    print(f"wall:    {wall.split(';')[0]}")
    print(f"spread:  {tracer.dependents(ref('B1'))}")

    engine.set_literal(ref("A2"), 5.0)
    healed = doctor.diagnose(ref("D1"))
    print(f"healed:  {healed}")
    print(f"result:  D1 = {engine.value(ref('D1'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
