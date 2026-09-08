from __future__ import annotations

from gridiron.refs import CellRef, RangeRef
from gridiron.setops import (
    KeyedRegion,
    difference,
    intersection,
    union,
)
from gridiron.sheet import Sheet


def keyed(values: list[object]) -> KeyedRegion:
    sheet = Sheet()
    for row, value in enumerate(values):
        if value is not None:
            sheet.set_literal(
                CellRef(row=row, col=0), value
            )
    area = RangeRef(
        top=0, left=0, bottom=len(values) - 1, right=0
    )
    return KeyedRegion(sheet=sheet, area=area, key_col=0)


class TestUnion:
    def test_first_region_then_new_from_second(self):
        left = keyed(["Ada", "Grace"])
        right = keyed(["Grace", "Alan"])
        result = union(left, right)
        assert result.labels() == ["Ada", "Grace", "Alan"]

    def test_the_note_counts(self):
        left = keyed(["a", "b"])
        right = keyed(["b", "c"])
        assert "3 in the union" in union(left, right).note


class TestIntersection:
    def test_only_the_shared_keys(self):
        left = keyed(["Ada", "Grace", "Alan"])
        right = keyed(["Grace", "Alan", "Edsger"])
        result = intersection(left, right)
        assert result.labels() == ["Grace", "Alan"]

    def test_order_follows_the_left_region(self):
        left = keyed(["Alan", "Grace"])
        right = keyed(["Grace", "Alan"])
        assert intersection(left, right).labels() == [
            "Alan",
            "Grace",
        ]


class TestDifference:
    def test_left_minus_right(self):
        left = keyed(["Ada", "Grace", "Alan"])
        right = keyed(["Grace"])
        result = difference(left, right)
        assert result.labels() == ["Ada", "Alan"]

    def test_the_dropped_names_are_the_churn(self):
        current = keyed(["Ada", "Grace", "Alan"])
        renewed = keyed(["Ada", "Alan"])
        churned = difference(current, renewed)
        assert churned.labels() == ["Grace"]


class TestKeyHygiene:
    def test_number_and_text_five_do_not_match(self):
        left = keyed([5.0])
        right = keyed(["5"])
        assert intersection(left, right).labels() == []

    def test_duplicates_collapse_before_the_operation(self):
        left = keyed(["a", "a", "b"])
        left.keys_in_order()
        assert left.dropped_duplicates == 1

    def test_blanks_are_excluded_not_matched(self):
        left = keyed([None, "a"])
        right = keyed([None, "b"])
        # Two blanks must not intersect into a phantom match.
        assert intersection(left, right).labels() == []
        left.keys_in_order()
        assert left.dropped_blanks == 1
