from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.sheet import Sheet
from gridiron.spill import SpillManager
from gridiron.values import is_error


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def manager() -> SpillManager:
    return SpillManager(sheet=Sheet())


class TestSpilling:
    def test_the_sequence_lands_whole(self):
        spills = manager()
        verdict = spills.spill_sequence(
            ref("A1"), count=4, start=10.0, step=5.0
        )
        assert verdict == "4 value(s) spilled from A1"
        assert spills.sheet.value_of(ref("A1")) == 10.0
        assert spills.sheet.value_of(ref("A4")) == 25.0

    def test_the_block_names_its_blocker(self):
        spills = manager()
        spills.sheet.set_literal(ref("A3"), "occupied")
        outcome = spills.spill_sequence(ref("A1"), count=4)
        assert is_error(outcome)
        assert "#SPILL! blocked by A3" in outcome.note
        assert "corruption arranged in a rectangle" in (
            outcome.note
        )
        assert spills.sheet.value_of(ref("A2")) is None

    def test_a_blocked_spill_does_not_partially_land(self):
        spills = manager()
        spills.sheet.set_literal(ref("A4"), 1.0)
        spills.spill_sequence(ref("A1"), count=5)
        assert spills.sheet.value_of(ref("A2")) is None
        assert spills.sheet.value_of(ref("A3")) is None


class TestGhosts:
    def test_editing_a_ghost_points_at_the_anchor(self):
        spills = manager()
        spills.spill_sequence(ref("A1"), count=3)
        with pytest.raises(Invalid) as caught:
            spills.edit_guard(ref("A2"))
        assert "spill ghost of A1" in str(caught.value)
        assert "fighting its shadow" in str(caught.value)

    def test_the_anchor_itself_is_editable(self):
        spills = manager()
        spills.spill_sequence(ref("A1"), count=3)
        spills.edit_guard(ref("A1"))

    def test_clearing_the_anchor_sweeps_the_ghosts(self):
        spills = manager()
        spills.spill_sequence(ref("A1"), count=4)
        verdict = spills.clear_anchor(ref("A1"))
        assert "3 ghost(s) swept" in verdict
        assert spills.sheet.value_of(ref("A2")) is None
        assert spills.ghosts == {}

    def test_clearing_a_non_anchor_is_refused(self):
        with pytest.raises(Invalid):
            manager().clear_anchor(ref("B1"))
