from __future__ import annotations

from gridiron.engine import Engine
from gridiron.errorhints import Diagnosis, ErrorDoctor
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def wounded_engine() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 10.0)
    engine.set_literal(ref("A2"), 0.0)
    engine.set_formula(ref("B1"), "=A1/A2")
    engine.set_formula(ref("C1"), "=B1*2")
    engine.set_formula(ref("D1"), "=C1+1")
    return engine


class TestDiagnosis:
    def test_the_origin_is_where_arithmetic_went_wrong(self):
        doctor = ErrorDoctor(engine=wounded_engine())
        diagnosis = doctor.diagnose(ref("D1"))
        assert isinstance(diagnosis, Diagnosis)
        assert diagnosis.code == "#DIV/0!"
        assert diagnosis.origin == ref("B1")
        assert diagnosis.path == ("D1", "C1", "B1")

    def test_the_line_reads_as_an_echo_with_a_trail(self):
        doctor = ErrorDoctor(engine=wounded_engine())
        line = doctor.diagnose(ref("D1")).line()
        assert "echoes from B1" in line
        assert "D1 <- C1 <- B1" in line
        assert "guard the denominator" in line

    def test_the_origin_says_born_here(self):
        doctor = ErrorDoctor(engine=wounded_engine())
        line = doctor.diagnose(ref("B1")).line()
        assert "born here" in line

    def test_a_healthy_cell_is_said_plainly(self):
        doctor = ErrorDoctor(engine=wounded_engine())
        assert doctor.diagnose(ref("A1")) == "A1 is healthy"

    def test_a_different_code_upstream_is_not_the_origin(self):
        engine = wounded_engine()
        engine.set_formula(ref("E1"), "=NOSUCHFN(1)")
        engine.set_formula(ref("F1"), "=E1+B1")
        doctor = ErrorDoctor(engine=engine)
        diagnosis = doctor.diagnose(ref("F1"))
        assert diagnosis.code == "#NAME?"
        assert diagnosis.origin == ref("E1")


class TestTheCensus:
    def test_one_bug_many_echoes(self):
        doctor = ErrorDoctor(engine=wounded_engine())
        census = doctor.census()
        assert "#DIV/0!: 1 born, 2 echo(es)" in census
        assert "1 distinct problem(s) to hunt" in census

    def test_two_codes_count_separately(self):
        engine = wounded_engine()
        engine.set_formula(ref("E1"), "=NOSUCHFN(1)")
        doctor = ErrorDoctor(engine=engine)
        census = doctor.census()
        assert "#NAME?: 1 born, 0 echo(es)" in census
        assert "2 distinct problem(s) to hunt" in census

    def test_a_clean_sheet_says_so(self):
        engine = Engine()
        engine.set_literal(ref("A1"), 1.0)
        engine.set_formula(ref("B1"), "=A1*2")
        doctor = ErrorDoctor(engine=engine)
        assert doctor.census() == "no errors on the sheet"

    def test_a_cycle_is_diagnosed_without_spinning(self):
        engine = Engine()
        engine.set_formula(ref("A1"), "=B1+1")
        engine.set_formula(ref("B1"), "=A1+1")
        doctor = ErrorDoctor(engine=engine)
        diagnosis = doctor.diagnose(ref("A1"))
        assert diagnosis.code == "#CYCLE!"
        assert "break the loop" in diagnosis.line()
