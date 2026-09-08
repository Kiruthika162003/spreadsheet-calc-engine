from __future__ import annotations

import pytest

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.pivot import PivotSpec, PivotTable
from gridiron.refs import CellRef, RangeRef
from gridiron.values import is_error

ROWS = (
    ("Region", "Quarter", "Sales"),
    ("East", "Q1", 100.0),
    ("East", "Q2", 150.0),
    ("West", "Q1", 200.0),
    ("West", "Q2", 50.0),
    ("East", "Q1", 300.0),
)


def filled_engine() -> Engine:
    engine = Engine()
    for row_index, row in enumerate(ROWS):
        for col_index, value in enumerate(row):
            engine.set_literal(
                CellRef(row=row_index, col=col_index), value
            )
    return engine


def table(spec: PivotSpec, engine: Engine | None = None):
    engine = engine or filled_engine()
    return PivotTable(
        sheet=engine.sheet,
        region=RangeRef.parse("A1:C6"),
        spec=spec,
    )


class TestGrouping:
    def test_rows_and_columns_bucket_the_records(self):
        report = table(
            PivotSpec(
                rows="Region",
                columns="Quarter",
                values="Sales",
            )
        ).build()
        assert report.row_labels == ["East", "West"]
        assert report.col_labels == ["Q1", "Q2"]
        assert report.cells[("East", "Q1")] == 400.0
        assert report.cells[("West", "Q2")] == 50.0

    def test_totals_land_on_both_edges(self):
        report = table(
            PivotSpec(
                rows="Region",
                columns="Quarter",
                values="Sales",
            )
        ).build()
        assert report.row_totals["East"] == 550.0
        assert report.col_totals["Q1"] == 600.0
        assert report.grand == 800.0

    def test_a_rows_only_pivot_uses_one_column(self):
        report = table(
            PivotSpec(rows="Quarter", values="Sales")
        ).build()
        assert report.col_labels == ["SALES"]
        assert report.cells[("Q1", "SALES")] == 600.0

    def test_field_names_fold_case(self):
        report = table(
            PivotSpec(rows="region", values="sales")
        ).build()
        assert report.row_totals["West"] == 250.0


class TestTheAverageOfAveragesQuestion:
    def test_the_grand_average_weighs_records(self):
        report = table(
            PivotSpec(
                rows="Region", values="Sales", agg="AVERAGE"
            )
        ).build()
        east = report.row_totals["East"]
        west = report.row_totals["West"]
        assert east == pytest.approx(550.0 / 3)
        assert west == 125.0
        mean_of_means = (east + west) / 2
        assert report.grand == 160.0
        assert report.grand != mean_of_means


class TestErrorPoisoning:
    def test_an_error_wrecks_its_buckets_and_no_others(self):
        engine = filled_engine()
        engine.set_formula(CellRef.parse("C3"), "=1/0")
        report = table(
            PivotSpec(
                rows="Region",
                columns="Quarter",
                values="Sales",
            ),
            engine,
        ).build()
        assert is_error(report.cells[("East", "Q2")])
        assert is_error(report.row_totals["East"])
        assert is_error(report.col_totals["Q2"])
        assert is_error(report.grand)
        assert report.cells[("East", "Q1")] == 400.0
        assert report.col_totals["Q1"] == 600.0


class TestAuthorMistakesRaise:
    def test_a_missing_field_names_the_menu(self):
        with pytest.raises(Invalid) as caught:
            table(
                PivotSpec(rows="Country", values="Sales")
            ).build()
        assert "REGION" in str(caught.value)

    def test_a_duplicate_header_is_ambiguous(self):
        engine = filled_engine()
        engine.set_literal(CellRef.parse("B1"), "Region")
        with pytest.raises(Invalid) as caught:
            table(
                PivotSpec(rows="Region", values="Sales"),
                engine,
            ).build()
        assert "ambiguous" in str(caught.value)

    def test_an_unknown_aggregation_lists_the_options(self):
        with pytest.raises(Invalid) as caught:
            table(
                PivotSpec(
                    rows="Region",
                    values="Sales",
                    agg="PRODUCT",
                )
            ).build()
        assert "SUM, COUNT, AVERAGE" in str(caught.value)

    def test_a_numeric_header_is_refused(self):
        engine = filled_engine()
        engine.set_literal(CellRef.parse("C1"), 7.0)
        with pytest.raises(Invalid) as caught:
            table(
                PivotSpec(rows="Region", values="Sales"),
                engine,
            ).build()
        assert "text header" in str(caught.value)


class TestRendering:
    def test_the_rendered_table_reads_like_a_table(self):
        text = table(
            PivotSpec(
                rows="Region",
                columns="Quarter",
                values="Sales",
            )
        ).render()
        lines = text.splitlines()
        assert lines[0].split() == [
            "REGION",
            "Q1",
            "Q2",
            "TOTAL",
        ]
        assert lines[1].split() == [
            "East",
            "400",
            "150",
            "550",
        ]
        assert lines[-1].split() == [
            "TOTAL",
            "600",
            "200",
            "800",
        ]

    def test_count_fills_every_bucket(self):
        text = table(
            PivotSpec(
                rows="Region",
                columns="Quarter",
                values="Sales",
                agg="COUNT",
            )
        ).render()
        assert "East" in text
        assert text.splitlines()[-1].split() == [
            "TOTAL",
            "3",
            "2",
            "5",
        ]
