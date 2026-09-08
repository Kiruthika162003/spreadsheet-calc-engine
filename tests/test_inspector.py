from __future__ import annotations

import pytest

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.inspector import Inspector, node_count
from gridiron.parser import parse_formula
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def model() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 1.0)
    engine.set_formula(ref("B1"), "=A1+1")
    engine.set_formula(ref("C1"), "=B1+1")
    engine.set_formula(ref("D1"), "=C1+1")
    engine.set_formula(ref("E1"), "=A1*2")
    engine.set_formula(ref("F1"), "=A1*3")
    return engine


class TestShape:
    def test_the_deepest_chain_names_its_end(self):
        verdict = Inspector(engine=model()).deepest_chain()
        assert verdict.startswith(
            "deepest chain: 3 link(s) ending at D1"
        )

    def test_the_load_bearing_wall_is_the_watched_cell(self):
        verdict = Inspector(
            engine=model()
        ).load_bearing_wall()
        assert verdict.startswith(
            "load-bearing wall: A1 with 3 watcher(s)"
        )

    def test_a_formulaless_workbook_is_a_table(self):
        engine = Engine()
        engine.set_literal(ref("A1"), 1.0)
        with pytest.raises(Invalid):
            Inspector(engine=engine).deepest_chain()


class TestComplexity:
    def test_node_count_measures_the_tree(self):
        assert node_count(parse_formula("=1+2*3")) == 5
        assert node_count(parse_formula("=SUM(A1:A9)")) == 2

    def test_the_program_wearing_a_cells_clothes(self):
        engine = model()
        engine.set_formula(
            ref("G1"),
            "=1+2+3+4+5+6+7+8+9+10+11+12+13+14+15",
        )
        alarms = Inspector(engine=engine).complexity_alarms()
        assert len(alarms) == 1
        assert alarms[0].startswith("G1:")
        assert "deserves a name and a test" in alarms[0]

    def test_modest_formulas_raise_no_alarm(self):
        assert Inspector(
            engine=model()
        ).complexity_alarms() == []


class TestErrors:
    def test_scrolled_past_is_not_resolved(self):
        engine = model()
        engine.set_formula(ref("H1"), "=1/0")
        census = Inspector(engine=engine).error_census()
        assert "1 cell(s) showing errors" in census
        assert "H1=#DIV/0!" in census

    def test_the_clean_book_says_so(self):
        assert Inspector(
            engine=model()
        ).error_census() == (
            "no cell currently shows an error"
        )
