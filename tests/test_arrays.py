from __future__ import annotations

import pytest

from gridiron.arrays import (
    ArrayLab,
    frequency,
    mmult,
    sort_column,
    transpose,
    unique_column,
)
from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.spill import SpillManager
from gridiron.values import is_error


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def lab_with(cells: dict[str, object]) -> ArrayLab:
    sheet = Sheet()
    for address, value in cells.items():
        sheet.set_literal(ref(address), value)
    return ArrayLab(
        sheet=sheet, spill=SpillManager(sheet=sheet)
    )


class TestTranspose:
    def test_rows_become_columns(self):
        assert transpose([[1.0, 2.0], [3.0, 4.0]]) == [
            [1.0, 3.0],
            [2.0, 4.0],
        ]

    def test_a_region_lands_transposed(self):
        lab = lab_with(
            {"A1": 1.0, "B1": 2.0, "A2": 3.0, "B2": 4.0}
        )
        verdict = lab.transpose_region(
            RangeRef.parse("A1:B2"), ref("D1")
        )
        assert verdict == "2x2 grid spilled from D1"
        assert lab.sheet.value_of(ref("E1")) == 3.0
        assert lab.sheet.value_of(ref("D2")) == 2.0

    def test_a_blocked_landing_names_the_blocker(self):
        lab = lab_with(
            {"A1": 1.0, "B1": 2.0, "D2": 99.0}
        )
        outcome = lab.transpose_region(
            RangeRef.parse("A1:B1"), ref("D1")
        )
        assert is_error(outcome)
        assert "blocked by D2" in outcome.note
        assert "#SPILL!" in outcome.note


class TestUnique:
    def test_first_seen_order_survives(self):
        column = [[3.0], [1.0], [3.0], [2.0], [1.0]]
        assert unique_column(column) == [
            [3.0],
            [1.0],
            [2.0],
        ]

    def test_deduplication_does_not_sort(self):
        lab = lab_with(
            {"A1": 9.0, "A2": 2.0, "A3": 9.0, "A4": 5.0}
        )
        lab.unique_region(RangeRef.parse("A1:A4"), ref("C1"))
        assert lab.sheet.value_of(ref("C1")) == 9.0
        assert lab.sheet.value_of(ref("C2")) == 2.0
        assert lab.sheet.value_of(ref("C3")) == 5.0

    def test_a_wide_region_is_refused(self):
        with pytest.raises(Invalid) as caught:
            unique_column([[1.0, 2.0]])
        assert "single column" in str(caught.value)


class TestSort:
    def test_empties_sink_both_directions(self):
        column = [[3.0], [None], [1.0]]
        assert sort_column(column) == [
            [1.0],
            [3.0],
            [None],
        ]
        assert sort_column(column, descending=True) == [
            [3.0],
            [1.0],
            [None],
        ]

    def test_mixed_types_have_no_honest_order(self):
        with pytest.raises(Invalid) as caught:
            sort_column([[1.0], ["apple"]])
        assert "no honest order" in str(caught.value)


class TestFrequency:
    def test_one_more_bucket_than_edges(self):
        data = [[1.0], [5.0], [9.0], [12.0], [2.0]]
        counts = frequency(data, [3.0, 10.0])
        assert counts == [[2.0], [2.0], [1.0]]

    def test_shuffled_edges_are_refused(self):
        with pytest.raises(Invalid) as caught:
            frequency([[1.0]], [10.0, 3.0])
        assert "must rise" in str(caught.value)

    def test_the_tail_is_not_dropped(self):
        counts = frequency([[100.0]], [1.0])
        assert counts == [[0.0], [1.0]]


class TestMmult:
    def test_the_textbook_product(self):
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[5.0, 6.0], [7.0, 8.0]]
        assert mmult(a, b) == [
            [19.0, 22.0],
            [43.0, 50.0],
        ]

    def test_disagreeing_shapes_quote_both(self):
        with pytest.raises(Invalid) as caught:
            mmult([[1.0, 2.0]], [[1.0, 2.0]])
        assert "1x2 times 1x2" in str(caught.value)

    def test_text_in_a_seat_poisons(self):
        result = mmult([[1.0, "x"]], [[1.0], [2.0]])
        assert is_error(result[0][0])

    def test_regions_multiply_and_land(self):
        lab = lab_with(
            {
                "A1": 1.0,
                "B1": 2.0,
                "A2": 3.0,
                "B2": 4.0,
                "D1": 5.0,
                "D2": 6.0,
            }
        )
        verdict = lab.mmult_regions(
            RangeRef.parse("A1:B2"),
            RangeRef.parse("D1:D2"),
            ref("F1"),
        )
        assert verdict == "2x1 grid spilled from F1"
        assert lab.sheet.value_of(ref("F1")) == 17.0
        assert lab.sheet.value_of(ref("F2")) == 39.0


class TestGridSpillContract:
    def test_ghosts_guard_their_anchor(self):
        lab = lab_with({"A1": 1.0, "B1": 2.0})
        lab.transpose_region(
            RangeRef.parse("A1:B1"), ref("D1")
        )
        with pytest.raises(Invalid) as caught:
            lab.spill.edit_guard(ref("D2"))
        assert "spill ghost of D1" in str(caught.value)

    def test_clearing_the_anchor_sweeps_the_grid(self):
        lab = lab_with(
            {"A1": 1.0, "B1": 2.0, "A2": 3.0, "B2": 4.0}
        )
        lab.transpose_region(
            RangeRef.parse("A1:B2"), ref("D1")
        )
        verdict = lab.spill.clear_anchor(ref("D1"))
        assert "3 ghost(s) swept" in verdict
        assert lab.sheet.value_of(ref("E2")) is None

    def test_a_ragged_grid_cannot_spill(self):
        lab = lab_with({"A1": 1.0})
        with pytest.raises(Invalid) as caught:
            lab.spill.spill_grid(
                ref("C1"), [[1.0, 2.0], [3.0]]
            )
        assert "ragged" in str(caught.value)
