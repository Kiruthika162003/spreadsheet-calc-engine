from __future__ import annotations

import pytest

from gridiron.binning import (
    equal_width,
    quantile_bins,
    total_count,
)
from gridiron.errors import Invalid

DATA = [float(n) for n in range(1, 11)]


class TestEqualWidth:
    def test_the_range_splits_evenly(self):
        buckets = equal_width(DATA, 2)
        assert buckets[0].label() == "[1, 5.5)"
        assert buckets[1].label() == "[5.5, 10]"

    def test_counts_sum_to_the_input(self):
        buckets = equal_width(DATA, 4)
        assert total_count(buckets) == len(DATA)

    def test_a_boundary_value_goes_up(self):
        buckets = equal_width([0.0, 5.0, 10.0], 2)
        assert buckets[0].count == 1
        assert buckets[1].count == 2

    def test_the_maximum_lands_in_the_last_bucket(self):
        buckets = equal_width(DATA, 5)
        assert buckets[-1].count >= 1
        assert total_count(buckets) == len(DATA)

    def test_a_flat_column_is_refused(self):
        with pytest.raises(Invalid) as caught:
            equal_width([5.0, 5.0, 5.0], 3)
        assert "not a distribution" in str(caught.value)


class TestQuantile:
    def test_each_bin_holds_a_similar_count(self):
        buckets = quantile_bins(DATA, 2)
        counts = [b.count for b in buckets]
        assert counts == [5, 5]
        assert total_count(buckets) == 10

    def test_more_bins_than_values_is_refused(self):
        with pytest.raises(Invalid) as caught:
            quantile_bins([1.0, 2.0], 5)
        assert "needs a home" in str(caught.value)

    def test_clustered_data_collapses_is_refused(self):
        with pytest.raises(Invalid) as caught:
            quantile_bins([5.0, 5.0, 5.0, 5.0], 2)
        assert "single count" in str(caught.value)


class TestRefusals:
    def test_zero_bins_is_refused(self):
        with pytest.raises(Invalid):
            equal_width(DATA, 0)

    def test_no_values_is_refused(self):
        with pytest.raises(Invalid):
            equal_width([], 3)
