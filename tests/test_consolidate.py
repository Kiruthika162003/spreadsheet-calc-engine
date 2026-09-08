from __future__ import annotations

import pytest

from gridiron.consolidate import Region, consolidate
from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import ErrorValue, is_error


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def region_from(
    pairs: list[tuple[object, object]],
) -> Region:
    sheet = Sheet()
    for row, (label, value) in enumerate(pairs):
        if label is not None:
            sheet.set_literal(CellRef(row=row, col=0), label)
        if value is not None:
            sheet.set_literal(CellRef(row=row, col=1), value)
    area = RangeRef(
        top=0, left=0, bottom=len(pairs) - 1, right=1
    )
    return Region(
        sheet=sheet, area=area, label_col=0, value_col=1
    )


class TestMatchingByLabel:
    def test_labels_combine_regardless_of_order(self):
        east = region_from(
            [("Widgets", 10.0), ("Gadgets", 20.0)]
        )
        west = region_from(
            [("Gadgets", 5.0), ("Widgets", 7.0)]
        )
        result = consolidate([east, west])
        assert result["Widgets"] == 17.0
        assert result["Gadgets"] == 25.0

    def test_first_seen_order_is_preserved(self):
        a = region_from([("B", 1.0), ("A", 2.0)])
        b = region_from([("C", 3.0)])
        result = consolidate([a, b])
        assert list(result) == ["B", "A", "C"]

    def test_a_label_missing_from_one_region(self):
        a = region_from([("X", 5.0)])
        b = region_from([("X", 3.0), ("Y", 9.0)])
        result = consolidate([a, b])
        assert result["X"] == 8.0
        assert result["Y"] == 9.0


class TestCombiners:
    def test_max_and_min_pick_extremes(self):
        a = region_from([("X", 5.0)])
        b = region_from([("X", 9.0)])
        assert consolidate([a, b], "MAX")["X"] == 9.0
        assert consolidate([a, b], "MIN")["X"] == 5.0

    def test_count_counts(self):
        a = region_from([("X", 5.0)])
        b = region_from([("X", 9.0)])
        assert consolidate([a, b], "COUNT")["X"] == 2.0

    def test_an_unknown_combiner_is_refused(self):
        a = region_from([("X", 5.0)])
        with pytest.raises(Invalid) as caught:
            consolidate([a], "AVERAGE")
        assert "unknown combiner" in str(caught.value)


class TestPoisonAndRefusals:
    def test_an_error_poisons_only_its_label(self):
        a = region_from([("X", 5.0), ("Y", 1.0)])
        a.sheet.set_literal(
            ref("B1"),
            ErrorValue(code="#DIV/0!", note="x"),
        )
        result = consolidate([a])
        assert is_error(result["X"])
        assert result["Y"] == 1.0

    def test_a_numeric_label_is_refused(self):
        bad = region_from([(100.0, 5.0)])
        with pytest.raises(Invalid) as caught:
            consolidate([bad])
        assert "merges account 100" in str(caught.value)

    def test_a_missing_value_is_not_a_zero(self):
        a = region_from([("X", None)])
        b = region_from([("X", 5.0)])
        # X appears with only one number; the blank does not
        # dilute it to an average or force a phantom zero.
        assert consolidate([a, b])["X"] == 5.0
