from __future__ import annotations

import pytest

from gridiron.dynarrays import DynamicArrays
from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.spill import SpillManager
from gridiron.values import ErrorValue, is_error


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def lab_with(cells: dict[str, object]) -> DynamicArrays:
    sheet = Sheet()
    for address, value in cells.items():
        sheet.set_literal(ref(address), value)
    return DynamicArrays(
        sheet=sheet, spill=SpillManager(sheet=sheet)
    )


def region(text: str) -> RangeRef:
    return RangeRef.parse(text)


class TestFilter:
    def test_truthy_rows_survive(self):
        lab = lab_with(
            {
                "A1": "east",
                "B1": 100.0,
                "A2": "west",
                "B2": 40.0,
                "A3": "north",
                "B3": 250.0,
                "C1": True,
                "C2": False,
                "C3": True,
            }
        )
        lab.filter(
            region("A1:B3"), region("C1:C3"), ref("E1")
        )
        assert lab.sheet.value_of(ref("E1")) == "east"
        assert lab.sheet.value_of(ref("E2")) == "north"
        assert lab.sheet.value_of(ref("F2")) == 250.0
        assert lab.sheet.value_of(ref("E3")) is None

    def test_a_mismatched_condition_is_refused(self):
        lab = lab_with(
            {"A1": 1.0, "A2": 2.0, "C1": True}
        )
        with pytest.raises(Invalid) as caught:
            lab.filter(
                region("A1:A2"), region("C1:C1"), ref("E1")
            )
        assert "drop the tail" in str(caught.value)

    def test_no_match_lands_the_fallback(self):
        lab = lab_with(
            {"A1": 1.0, "A2": 2.0, "C1": False, "C2": False}
        )
        lab.filter(
            region("A1:A2"),
            region("C1:C2"),
            ref("E1"),
            fallback="none",
        )
        assert lab.sheet.value_of(ref("E1")) == "none"

    def test_no_match_and_no_fallback_is_refused(self):
        lab = lab_with(
            {"A1": 1.0, "C1": False}
        )
        with pytest.raises(Invalid) as caught:
            lab.filter(
                region("A1:A1"), region("C1:C1"), ref("E1")
            )
        assert "needs somewhere to be shown" in str(
            caught.value
        )

    def test_an_error_poisons_the_whole_filter(self):
        lab = lab_with(
            {"A1": 1.0, "A2": 2.0, "C1": True, "C2": True}
        )
        lab.sheet.set_literal(
            ref("A2"),
            ErrorValue(code="#DIV/0!", note="x"),
        )
        outcome = lab.filter(
            region("A1:A2"), region("C1:C2"), ref("E1")
        )
        assert is_error(outcome)


class TestSortBy:
    def test_rows_order_by_a_hidden_key(self):
        lab = lab_with(
            {
                "A1": "Ada",
                "A2": "Grace",
                "A3": "Alan",
                "K1": 30.0,
                "K2": 10.0,
                "K3": 20.0,
            }
        )
        lab.sortby(
            region("A1:A3"), region("K1:K3"), ref("E1")
        )
        assert lab.sheet.value_of(ref("E1")) == "Grace"
        assert lab.sheet.value_of(ref("E2")) == "Alan"
        assert lab.sheet.value_of(ref("E3")) == "Ada"

    def test_descending_reverses_the_order(self):
        lab = lab_with(
            {
                "A1": "Ada",
                "A2": "Grace",
                "A3": "Alan",
                "K1": 30.0,
                "K2": 10.0,
                "K3": 20.0,
            }
        )
        lab.sortby(
            region("A1:A3"),
            region("K1:K3"),
            ref("E1"),
            descending=True,
        )
        assert lab.sheet.value_of(ref("E1")) == "Ada"
        assert lab.sheet.value_of(ref("E3")) == "Grace"

    def test_equal_keys_keep_arrival_order(self):
        lab = lab_with(
            {
                "A1": "first",
                "A2": "second",
                "A3": "third",
                "K1": 5.0,
                "K2": 5.0,
                "K3": 5.0,
            }
        )
        lab.sortby(
            region("A1:A3"), region("K1:K3"), ref("E1")
        )
        assert lab.sheet.value_of(ref("E1")) == "first"
        assert lab.sheet.value_of(ref("E2")) == "second"
        assert lab.sheet.value_of(ref("E3")) == "third"

    def test_a_mismatched_key_is_refused(self):
        lab = lab_with(
            {"A1": "x", "A2": "y", "K1": 1.0}
        )
        with pytest.raises(Invalid) as caught:
            lab.sortby(
                region("A1:A2"), region("K1:K1"), ref("E1")
            )
        assert "one key per row" in str(caught.value)
