from __future__ import annotations

import pytest

from gridiron.engine import Engine
from gridiron.errors import Invalid, Missing
from gridiron.refs import CellRef
from gridiron.scenarios import ScenarioManager


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def model() -> ScenarioManager:
    engine = Engine()
    engine.set_literal(ref("A1"), 100.0)
    engine.set_literal(ref("A2"), 0.1)
    engine.set_formula(ref("C1"), "=A1*(1+A2)")
    manager = ScenarioManager(engine=engine)
    manager.capture("baseline", (ref("A1"), ref("A2")))
    engine.set_literal(ref("A1"), 150.0)
    engine.set_literal(ref("A2"), 0.25)
    manager.capture("boom", (ref("A1"), ref("A2")))
    return manager


class TestCaptureAndApply:
    def test_applying_swaps_every_input_together(self):
        manager = model()
        manager.apply("baseline")
        assert manager.engine.value(ref("C1")) == pytest.approx(
            110.0
        )
        manager.apply("boom")
        assert manager.engine.value(ref("C1")) == pytest.approx(
            187.5
        )

    def test_capturing_a_formula_cell_is_refused(self):
        manager = model()
        with pytest.raises(Invalid) as caught:
            manager.capture("bad", (ref("C1"),))
        assert "different verbs" in str(caught.value)

    def test_names_are_captured_once(self):
        manager = model()
        with pytest.raises(Invalid):
            manager.capture("boom", (ref("A1"),))

    def test_the_missing_scenario_is_missing(self):
        with pytest.raises(Missing):
            model().apply("bust")

    def test_a_grown_formula_blocks_the_apply(self):
        manager = model()
        manager.engine.set_formula(ref("A1"), "=1")
        with pytest.raises(Invalid) as caught:
            manager.apply("baseline")
        assert "grew a formula since" in str(caught.value)


class TestTheFridayTable:
    def test_the_summary_tabulates_watched_outputs(self):
        manager = model()
        table = manager.summary(
            watched=(ref("C1"),),
            names=("baseline", "boom"),
        )
        assert table.startswith(
            "the Friday table, built by machine:"
        )
        assert "baseline: C1=110" in table
        assert "boom: C1=187.5" in table

    def test_an_empty_summary_is_refused(self):
        with pytest.raises(Invalid):
            model().summary(watched=(), names=("boom",))
