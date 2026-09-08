from __future__ import annotations

import pytest

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.macros import MacroRecorder
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def recorded() -> MacroRecorder:
    macro = MacroRecorder()
    macro.record_literal(ref("A1"), 10.0)
    macro.record_literal(ref("A2"), 20.0)
    macro.record_formula(ref("A3"), "=A1+A2")
    return macro


class TestReplay:
    def test_a_macro_replays_on_a_fresh_sheet(self):
        macro = recorded()
        engine = Engine()
        verdict = macro.replay(engine)
        assert "replayed 3 step(s)" in verdict
        assert engine.value(ref("A3")) == 30.0

    def test_the_same_macro_replays_on_another_sheet(self):
        macro = recorded()
        first, second = Engine(), Engine()
        macro.replay(first)
        macro.replay(second)
        assert first.value(ref("A3")) == second.value(
            ref("A3")
        )

    def test_intent_not_values_is_recorded(self):
        macro = recorded()
        engine = Engine()
        engine.set_literal(ref("A1"), 999.0)
        # Replaying overwrites A1 with the recorded 10, then
        # A3 recomputes from the recorded inputs, not the
        # stale 999.
        macro.replay(engine)
        assert engine.value(ref("A3")) == 30.0


class TestRelocation:
    def test_a_shift_relocates_cells_and_formulas(self):
        macro = recorded()
        engine = Engine()
        macro.replay(engine, rows=9, cols=3)
        assert engine.value(ref("D10")) == 10.0
        assert engine.value(ref("D11")) == 20.0
        assert engine.value(ref("D12")) == 30.0

    def test_the_relocated_formula_points_correctly(self):
        macro = recorded()
        engine = Engine()
        macro.replay(engine, rows=9, cols=3)
        cell = engine.sheet.cell(ref("D12"))
        assert cell.formula_text == "=(D10+D11)"

    def test_a_shift_off_the_edge_is_refused(self):
        macro = recorded()
        engine = Engine()
        with pytest.raises(Invalid) as caught:
            macro.replay(engine, rows=-5, cols=0)
        assert "half-applies" in str(caught.value)

    def test_the_refusal_applies_nothing(self):
        macro = recorded()
        engine = Engine()
        with pytest.raises(Invalid):
            macro.replay(engine, rows=-5, cols=0)
        assert engine.sheet.cell(ref("A1")) is None


class TestClearAndDescribe:
    def test_a_clear_step_replays(self):
        macro = MacroRecorder()
        macro.record_literal(ref("A1"), 5.0)
        macro.record_clear(ref("A1"))
        engine = Engine()
        macro.replay(engine)
        assert engine.sheet.cell(ref("A1")) is None

    def test_describe_reads_the_recording(self):
        text = recorded().describe()
        assert "A1 = 10.0" in text
        assert "A3: =A1+A2" in text
