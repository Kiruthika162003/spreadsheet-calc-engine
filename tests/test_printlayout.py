from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.printlayout import PrintPlanner
from gridiron.refs import CellRef, RangeRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def planner(**overrides) -> PrintPlanner:
    settings = {
        "region": RangeRef.parse("A1:F100"),
        "rows_per_page": 40,
        "cols_per_page": 3,
    }
    settings.update(overrides)
    return PrintPlanner(**settings)


class TestTheTiling:
    def test_down_then_over(self):
        pages = planner().paginate()
        assert len(pages) == 6
        assert (pages[0].top, pages[0].bottom) == (0, 39)
        assert (pages[1].top, pages[1].bottom) == (40, 79)
        assert (pages[2].top, pages[2].bottom) == (80, 99)
        assert pages[0].left == pages[2].left == 0
        assert pages[3].left == 3
        assert pages[3].top == 0

    def test_every_cell_finds_its_page(self):
        plan = planner()
        assert plan.page_of(ref("A1")) == 1
        assert plan.page_of(ref("C55")) == 2
        assert plan.page_of(ref("F100")) == 6

    def test_outside_the_region_is_refused(self):
        with pytest.raises(Invalid) as caught:
            planner().page_of(ref("Z1"))
        assert "outside the print region" in str(
            caught.value
        )


class TestHeaderRent:
    def test_every_page_pays_the_same_rent(self):
        plan = planner(header_rows=5)
        pages = plan.paginate()
        first_height = pages[0].bottom - pages[0].top + 1
        second_height = pages[1].bottom - pages[1].top + 1
        assert first_height == 35
        assert second_height == 35
        assert pages[0].top == 5

    def test_later_pages_are_marked_with_the_reprint(self):
        pages = planner(header_rows=5).paginate()
        assert not pages[0].repeated_header
        assert pages[1].repeated_header
        assert "(+header)" in pages[1].describe()

    def test_a_header_cell_has_no_single_home(self):
        plan = planner(header_rows=5)
        with pytest.raises(Invalid) as caught:
            plan.page_of(ref("B3"))
        assert "no single home" in str(caught.value)

    def test_the_header_that_ate_the_page(self):
        with pytest.raises(Invalid) as caught:
            planner(rows_per_page=10, header_rows=10)
        assert "stationery" in str(caught.value)


class TestBreaks:
    def test_a_break_starts_a_fresh_page(self):
        plan = planner()
        plan.add_break_before_row(25)
        pages = plan.paginate()
        assert (pages[0].top, pages[0].bottom) == (0, 24)
        assert pages[1].top == 25

    def test_breaks_and_capacity_compose(self):
        plan = planner()
        plan.add_break_before_row(25)
        pages = plan.paginate()
        assert (pages[1].top, pages[1].bottom) == (25, 64)
        assert (pages[2].top, pages[2].bottom) == (65, 99)
        assert len(pages) == 6

    def test_a_break_outside_the_region_is_a_typo(self):
        with pytest.raises(Invalid) as caught:
            planner().add_break_before_row(500)
        assert "needs a place to stand" in str(caught.value)


class TestThePlan:
    def test_the_plan_reads_as_a_page_list(self):
        plan = planner(header_rows=5).plan()
        lines = plan.splitlines()
        assert lines[0] == "Page 1: rows 6-40, cols A-C"
        assert lines[1] == (
            "Page 2: rows 41-75, cols A-C (+header)"
        )
        assert lines[-1].endswith("down then over")

    def test_a_zero_area_page_is_refused(self):
        with pytest.raises(Invalid):
            planner(rows_per_page=0)
