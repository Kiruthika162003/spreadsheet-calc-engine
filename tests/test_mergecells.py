from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.mergecells import MergeRegistry
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def registry() -> MergeRegistry:
    sheet = Sheet()
    sheet.set_literal(ref("A1"), "Quarterly Report")
    built = MergeRegistry(sheet=sheet)
    built.merge(RangeRef.parse("A1:D1"))
    return built


class TestMerging:
    def test_the_anchor_is_the_only_real_cell(self):
        built = registry()
        assert built.anchor_of(ref("C1")).a1() == "A1"
        assert built.anchor_of(ref("A2")) is None

    def test_merging_over_data_is_against_the_religion(self):
        sheet = Sheet()
        sheet.set_literal(ref("B1"), "occupied")
        with pytest.raises(Invalid) as caught:
            MergeRegistry(sheet=sheet).merge(
                RangeRef.parse("A1:D1")
            )
        assert "against this house's religion" in str(
            caught.value
        )

    def test_merges_do_not_stack(self):
        built = registry()
        with pytest.raises(Invalid) as caught:
            built.merge(RangeRef.parse("C1:E1"))
        assert "merges do not stack" in str(caught.value)

    def test_the_one_cell_merge_is_a_costume(self):
        with pytest.raises(Invalid):
            MergeRegistry(sheet=Sheet()).merge(
                RangeRef.parse("A1:A1")
            )


class TestWrites:
    def test_covered_cells_redirect_to_the_anchor(self):
        built = registry()
        with pytest.raises(Invalid) as caught:
            built.check_write(ref("B1"))
        assert "anchored at A1" in str(caught.value)
        assert "where the value really lives" in str(
            caught.value
        )

    def test_the_anchor_itself_writes_freely(self):
        registry().check_write(ref("A1"))


class TestUnmerging:
    def test_the_value_stays_with_the_anchor(self):
        built = registry()
        verdict = built.unmerge(RangeRef.parse("A1:D1"))
        assert "stays with A1" in verdict
        assert built.sheet.value_of(ref("A1")) == (
            "Quarterly Report"
        )
        assert built.regions == []

    def test_unmerging_a_stranger_is_refused(self):
        with pytest.raises(Invalid):
            registry().unmerge(RangeRef.parse("F1:G1"))

    def test_the_census_lists_anchors(self):
        census = registry().census()
        assert "A1:D1 anchored at A1" in census
