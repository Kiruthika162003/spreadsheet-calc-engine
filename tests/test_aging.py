from __future__ import annotations

import pytest

from gridiron.aging import age_balances
from gridiron.errors import Invalid

ITEMS = [
    (100.0, 5),
    (200.0, 35),
    (50.0, 30),
    (300.0, 120),
    (-25.0, -3),
    (40.0, 0),
]


class TestBucketing:
    def test_each_balance_lands_in_one_bucket(self):
        report = age_balances(ITEMS)
        assert report.buckets["0-30"] == 140.0
        assert report.buckets["30-60"] == 250.0
        assert report.buckets["90+"] == 300.0

    def test_the_report_reconciles_to_the_total(self):
        report = age_balances(ITEMS)
        assert report.total == 665.0
        assert report.reconciles()

    def test_a_boundary_day_lands_in_the_upper_bucket(self):
        # 30 days lands in 30-60, not in 0-30.
        report = age_balances([(50.0, 30)])
        assert report.buckets["0-30"] == 0.0
        assert report.buckets["30-60"] == 50.0


class TestSpecialBalances:
    def test_not_yet_due_is_its_own_bucket(self):
        report = age_balances([(100.0, -5)])
        assert report.buckets["not due"] == 100.0
        assert report.buckets["0-30"] == 0.0

    def test_a_credit_still_ties_to_the_total(self):
        report = age_balances([(100.0, 10), (-30.0, 10)])
        assert report.buckets["0-30"] == 70.0
        assert report.reconciles()


class TestBoundaries:
    def test_a_custom_ladder(self):
        report = age_balances(
            [(10.0, 8), (20.0, 20)],
            boundaries=(0, 7, 14),
        )
        # 8 days lands in 7-14; 20 days in 14+.
        assert report.buckets["0-7"] == 0.0
        assert report.buckets["7-14"] == 10.0
        assert report.buckets["14+"] == 20.0

    def test_an_unsorted_ladder_is_refused(self):
        with pytest.raises(Invalid) as caught:
            age_balances(ITEMS, boundaries=(0, 60, 30))
        assert "must rise" in str(caught.value)

    def test_a_ladder_not_starting_at_zero(self):
        with pytest.raises(Invalid) as caught:
            age_balances(ITEMS, boundaries=(10, 30))
        assert "day zero" in str(caught.value)
