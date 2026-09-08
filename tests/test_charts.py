from __future__ import annotations

import pytest

from gridiron.charts import (
    BarChart,
    Series,
    nice_step,
    nice_ticks,
    sparkline,
)
from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def sales_sheet() -> Sheet:
    sheet = Sheet()
    for address, value in (
        ("A1", "Sales"),
        ("A2", 12.0),
        ("A3", 47.0),
        ("A4", 33.0),
        ("A5", 97.0),
    ):
        sheet.set_literal(ref(address), value)
    return sheet


class TestTheLadder:
    def test_steps_round_at_the_classic_midpoints(self):
        assert nice_step(1.3) == 1
        assert nice_step(3.7) == 5
        assert nice_step(6.0) == 5
        assert nice_step(24.25) == 20
        assert nice_step(0.13) == pytest.approx(0.1)

    def test_ticks_read_at_a_glance(self):
        assert nice_ticks(0.0, 97.0) == [
            0.0,
            20.0,
            40.0,
            60.0,
            80.0,
            100.0,
        ]

    def test_a_flat_axis_still_stands_up(self):
        ticks = nice_ticks(5.0, 5.0)
        assert ticks[0] <= 5.0 <= ticks[-1]

    def test_an_upside_down_axis_is_refused(self):
        with pytest.raises(Invalid) as caught:
            nice_ticks(10.0, 1.0)
        assert "upside down" in str(caught.value)


class TestSeries:
    def test_the_header_names_the_series(self):
        series = Series.from_column(
            sales_sheet(), RangeRef.parse("A1:A5")
        )
        assert series.name == "Sales"
        assert series.values == (12.0, 47.0, 33.0, 97.0)

    def test_a_wounded_cell_refuses_the_whole_chart(self):
        sheet = sales_sheet()
        engine = Engine(sheet=sheet)
        engine.set_formula(ref("A3"), "=1/0")
        with pytest.raises(Invalid) as caught:
            Series.from_column(sheet, RangeRef.parse("A1:A5"))
        assert "A3 holds #DIV/0!" in str(caught.value)

    def test_an_empty_series_is_refused(self):
        sheet = Sheet()
        sheet.set_literal(ref("A1"), "Empty")
        with pytest.raises(Invalid) as caught:
            Series.from_column(sheet, RangeRef.parse("A1:A4"))
        assert "pretending to be information" in str(
            caught.value
        )

    def test_a_wide_region_is_not_a_series(self):
        with pytest.raises(Invalid) as caught:
            Series.from_column(
                sales_sheet(), RangeRef.parse("A1:B5")
            )
        assert "one column" in str(caught.value)


class TestBars:
    def test_proportions_are_countable(self):
        chart = BarChart(
            series=Series(
                name="Q", values=(50.0, 100.0)
            ),
            width=20,
        )
        lines = chart.render().splitlines()
        assert lines[0] == "Q (0 to 100)"
        assert lines[1].count("#") == 10
        assert lines[2].count("#") == 20

    def test_a_bad_quarter_cannot_hide(self):
        chart = BarChart(
            series=Series(
                name="Growth", values=(40.0, -20.0)
            ),
            width=30,
        )
        lines = chart.render().splitlines()
        assert "-" in lines[2]
        assert "#" not in lines[2]

    def test_bars_share_one_axis(self):
        chart = BarChart(
            series=Series(
                name="S", values=(97.0, 12.0)
            ),
            width=40,
        )
        lines = chart.render().splitlines()
        assert lines[0].endswith("(0 to 100)")
        assert lines[1].count("#") == round(97 / 100 * 40)


class TestSparklines:
    def test_the_depth_marks_map_min_to_max(self):
        line = sparkline(
            Series(name="Trend", values=(1.0, 5.0, 9.0))
        )
        assert line.startswith("Trend: [")
        marks = line.split("[")[1].split("]")[0]
        assert marks[0] == " "
        assert marks[-1] == "#"
        assert line.endswith("1 to 9")

    def test_a_flat_series_says_so(self):
        line = sparkline(
            Series(name="Flat", values=(4.0, 4.0, 4.0))
        )
        assert "flat at 4" in line
        assert "###" in line
