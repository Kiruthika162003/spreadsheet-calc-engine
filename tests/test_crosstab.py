from __future__ import annotations

from gridiron.crosstab import crosstab_count, crosstab_sum

COUNT_RECORDS = [
    ("East", "Q1"),
    ("East", "Q1"),
    ("West", "Q1"),
    ("East", "Q2"),
]
SUM_RECORDS = [
    ("East", "Q1", 100.0),
    ("East", "Q1", 50.0),
    ("West", "Q1", "n/a"),
    ("East", "Q2", 30.0),
]


class TestCount:
    def test_cells_count_records(self):
        table = crosstab_count(COUNT_RECORDS)
        assert table.cell("East", "Q1") == 2.0
        assert table.cell("West", "Q1") == 1.0

    def test_labels_are_sorted(self):
        table = crosstab_count(COUNT_RECORDS)
        assert table.rows() == ["East", "West"]
        assert table.columns() == ["Q1", "Q2"]

    def test_the_margins_tie(self):
        table = crosstab_count(COUNT_RECORDS)
        assert table.row_total("East") == 3.0
        assert table.column_total("Q1") == 3.0
        assert table.grand_total() == 4.0
        # Margins reconcile to the grand total.
        assert sum(
            table.row_total(r) for r in table.rows()
        ) == table.grand_total()


class TestSum:
    def test_cells_sum_the_value(self):
        table = crosstab_sum(SUM_RECORDS)
        assert table.cell("East", "Q1") == 150.0

    def test_non_numeric_records_are_excluded(self):
        table = crosstab_sum(SUM_RECORDS)
        assert table.excluded == 1
        assert table.grand_total() == 180.0

    def test_the_excluded_do_not_vanish_silently(self):
        # The count of dropped records is reported, not zero.
        table = crosstab_sum(SUM_RECORDS)
        assert table.excluded > 0


class TestEmpty:
    def test_an_empty_table_is_not_an_error(self):
        table = crosstab_count([])
        assert table.grand_total() == 0
        assert table.rows() == []
