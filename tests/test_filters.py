from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.filters import FilterView
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet


def ledger() -> Sheet:
    sheet = Sheet()
    rows = [
        ("item", "status", 0.0),
        ("apples", "open", 40.0),
        ("bread", "closed", 15.0),
        ("cheese", "open", 8.0),
        ("dates", "open", 22.0),
    ]
    for offset, (item, status, amount) in enumerate(rows):
        sheet.set_literal(CellRef(row=offset, col=0), item)
        sheet.set_literal(
            CellRef(row=offset, col=1), status
        )
        sheet.set_literal(
            CellRef(row=offset, col=2), amount
        )
    return sheet


def view() -> FilterView:
    return FilterView(
        sheet=ledger(), region=RangeRef.parse("A1:C5")
    )


class TestTheGlasses:
    def test_criteria_hide_without_moving(self):
        filtered = view()
        filtered.add_criterion(1, "open")
        assert filtered.visible_rows() == [0, 1, 3, 4]
        assert filtered.hidden_count() == 1
        assert filtered.sheet.value_of(
            CellRef(row=2, col=0)
        ) == "bread"

    def test_columns_stack_with_and_semantics(self):
        filtered = view()
        filtered.add_criterion(1, "open")
        filtered.add_criterion(2, ">20")
        assert filtered.visible_rows() == [0, 1, 4]

    def test_the_header_row_is_exempt_by_construction(self):
        filtered = view()
        filtered.add_criterion(1, "open")
        assert 0 in filtered.visible_rows()

    def test_clearing_restores_because_nothing_was_gone(self):
        filtered = view()
        filtered.add_criterion(1, "closed")
        verdict = filtered.clear_criteria()
        assert "nothing was ever gone" in verdict
        assert len(filtered.visible_rows()) == 5

    def test_criteria_outside_the_region_are_refused(self):
        with pytest.raises(Invalid):
            view().add_criterion(9, "open")


class TestTheClassicSilentError:
    def test_the_difference_belongs_on_the_page(self):
        filtered = view()
        filtered.add_criterion(1, "open")
        verdict = filtered.visible_sum(2)
        assert verdict.startswith("visible 70.0 of 85.0 total")
        assert "not in a meeting" in verdict
