from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.protection import Protection
from gridiron.refs import CellRef, RangeRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def guarded() -> Protection:
    protection = Protection()
    protection.lock(
        RangeRef.parse("A1:D9"),
        reason="closed period, see finance",
    )
    protection.punch_exception(RangeRef.parse("B2:B3"))
    return protection


class TestLocks:
    def test_the_refusal_is_an_explanation(self):
        with pytest.raises(Invalid) as caught:
            guarded().check_edit(ref("A1"))
        assert "closed period, see finance" in str(
            caught.value
        )

    def test_a_reasonless_lock_is_an_obstacle(self):
        with pytest.raises(Invalid):
            Protection().lock(RangeRef.parse("A1:A2"), "  ")

    def test_cells_outside_every_lock_are_free(self):
        guarded().check_edit(ref("Z9"))


class TestExceptions:
    def test_the_punched_input_cells_stay_editable(self):
        guarded().check_edit(ref("B2"))
        guarded().check_edit(ref("B3"))

    def test_an_exception_needs_a_lock_around_it(self):
        with pytest.raises(Invalid) as caught:
            Protection().punch_exception(
                RangeRef.parse("B2:B3")
            )
        assert "something to except from" in str(caught.value)


class TestTheExpiringUnlock:
    def test_the_unlock_spends_its_budget_and_relocks(self):
        protection = guarded()
        verdict = protection.unlock_all(edit_budget=2)
        assert "becomes the permanent state" in verdict
        protection.check_edit(ref("A1"))
        protection.check_edit(ref("A2"))
        with pytest.raises(Invalid):
            protection.check_edit(ref("A3"))

    def test_the_budget_must_be_positive(self):
        with pytest.raises(Invalid):
            guarded().unlock_all(edit_budget=0)


class TestTheCensus:
    def test_the_census_lists_locks_and_exceptions(self):
        census = guarded().census()
        assert "A1:D9: closed period, see finance" in census
        assert "except B2:B3: input cells" in census

    def test_the_unlocked_sheet_is_a_tuesday_risk(self):
        assert "every cell is a Tuesday risk" in (
            Protection().census()
        )
