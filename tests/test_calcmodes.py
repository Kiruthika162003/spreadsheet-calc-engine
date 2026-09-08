from __future__ import annotations

import pytest

from gridiron.calcmodes import CalcController
from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def controller() -> CalcController:
    control = CalcController(engine=Engine())
    control.set_literal(ref("A1"), 10.0)
    control.set_formula(ref("B1"), "=A1*2")
    control.set_formula(ref("C1"), "=B1+5")
    return control


class TestAutomaticMode:
    def test_auto_is_the_default_promise(self):
        control = controller()
        assert control.value(ref("C1")) == 25.0

    def test_calculate_belongs_to_manual(self):
        control = controller()
        with pytest.raises(Invalid) as caught:
            control.calculate()
        assert "never owes a recalc" in str(caught.value)


class TestDeferral:
    def test_edits_land_but_formulas_wait(self):
        control = controller()
        control.set_manual()
        verdict = control.set_literal(ref("A1"), 100.0)
        assert "deferred" in verdict
        assert control.value(ref("A1")) == 100.0
        assert control.value(ref("B1")) == 20.0
        assert control.value(ref("C1")) == 25.0

    def test_calculate_settles_the_whole_ledger(self):
        control = controller()
        control.set_manual()
        control.set_literal(ref("A1"), 100.0)
        report = control.calculate()
        assert sorted(report.evaluated) == ["B1", "C1"]
        assert control.value(ref("C1")) == 205.0

    def test_the_ledger_batches_across_edits(self):
        control = controller()
        control.set_manual()
        control.set_literal(ref("A1"), 50.0)
        control.set_literal(ref("A1"), 100.0)
        report = control.calculate()
        assert len(report.evaluated) == 2
        assert control.pending_report() == (
            "0 edit(s) deferred; 0 formula(s) stale"
        )


class TestStaleness:
    def test_staleness_is_queryable_by_cell(self):
        control = controller()
        control.set_manual()
        control.set_literal(ref("A1"), 100.0)
        assert control.is_stale(ref("B1"))
        assert control.is_stale(ref("C1"))
        assert not control.is_stale(ref("D9"))

    def test_the_pending_report_counts_both_kinds(self):
        control = controller()
        control.set_manual()
        control.set_literal(ref("A1"), 100.0)
        assert control.pending_report() == (
            "1 edit(s) deferred; 2 formula(s) stale"
        )

    def test_a_new_formula_is_stale_until_calculated(self):
        control = controller()
        control.set_manual()
        control.set_formula(ref("D1"), "=C1*10")
        assert control.is_stale(ref("D1"))
        assert control.value(ref("D1")) is None
        control.calculate()
        assert control.value(ref("D1")) == 250.0


class TestTheSwitchBack:
    def test_going_automatic_settles_first(self):
        control = controller()
        control.set_manual()
        control.set_literal(ref("A1"), 100.0)
        verdict = control.set_auto()
        assert "settling the ledger" in verdict
        assert control.value(ref("C1")) == 205.0

    def test_the_modes_announce_themselves(self):
        control = controller()
        assert "ledger remembers" in control.set_manual()
        assert "already manual" in control.set_manual()
        control.set_auto()
        assert control.set_auto() == "already automatic"
