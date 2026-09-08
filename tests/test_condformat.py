from __future__ import annotations

import pytest

from gridiron.condformat import ConditionalFormats
from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def dashboard() -> ConditionalFormats:
    sheet = Sheet()
    sheet.set_literal(ref("A1"), 95.0)
    sheet.set_literal(ref("A2"), 45.0)
    sheet.set_literal(ref("A3"), 10.0)
    formats = ConditionalFormats(sheet=sheet)
    formats.add_rule(
        1, RangeRef.parse("A1:A9"), "<20", "red",
        stop_if_true=True,
    )
    formats.add_rule(
        2, RangeRef.parse("A1:A9"), "<50", "yellow"
    )
    formats.add_rule(
        3, RangeRef.parse("A1:A9"), "<100", "green"
    )
    return formats


class TestTheCascade:
    def test_rules_apply_in_priority_order(self):
        formats = dashboard()
        assert formats.styles_for(ref("A2")) == [
            "yellow", "green",
        ]

    def test_stop_if_true_means_stop(self):
        formats = dashboard()
        assert formats.styles_for(ref("A3")) == ["red"]

    def test_cells_outside_every_region_are_unstyled(self):
        assert dashboard().styles_for(ref("Z9")) == []

    def test_priority_ties_would_be_a_coin_flip(self):
        formats = dashboard()
        with pytest.raises(Invalid) as caught:
            formats.add_rule(
                2, RangeRef.parse("A1:A2"), ">0", "blue"
            )
        assert "a coin flip" in str(caught.value)

    def test_a_styleless_rule_is_refused(self):
        with pytest.raises(Invalid):
            ConditionalFormats(sheet=Sheet()).add_rule(
                1, RangeRef.parse("A1:A2"), ">0", "  "
            )


class TestTheCensus:
    def test_dead_rules_and_crowded_cells_are_named(self):
        formats = dashboard()
        formats.add_rule(
            4, RangeRef.parse("A1:A9"), ">9000", "gold"
        )
        census = formats.census()
        assert "dead weight: priority 4" in census
        assert "worth deleting" in census

    def test_the_earning_rule_set_reads_clean(self):
        sheet = Sheet()
        sheet.set_literal(ref("A1"), 5.0)
        formats = ConditionalFormats(sheet=sheet)
        formats.add_rule(
            1, RangeRef.parse("A1:A1"), "<10", "red"
        )
        assert formats.census() == (
            "every rule earns its place"
        )
