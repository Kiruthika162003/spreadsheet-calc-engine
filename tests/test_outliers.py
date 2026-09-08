from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.outliers import (
    iqr_outliers,
    zscore_of,
    zscore_outliers,
)

DATA = [10.0, 11.0, 12.0, 11.0, 10.0, 12.0, 100.0]


class TestIqr:
    def test_it_flags_the_extreme(self):
        assert iqr_outliers(DATA) == [6]

    def test_a_clean_set_flags_nothing(self):
        assert iqr_outliers([1.0, 2.0, 3.0, 4.0, 5.0]) == []

    def test_too_few_values_are_refused(self):
        with pytest.raises(Invalid) as caught:
            iqr_outliers([1.0, 2.0, 3.0])
        assert "at least four" in str(caught.value)


class TestZScore:
    def test_it_can_miss_what_iqr_catches(self):
        # The outlier inflates its own standard deviation, so
        # its z-score stays under 3 and z-score misses it
        # while IQR flags it. The disagreement is the point.
        assert iqr_outliers(DATA) == [6]
        assert zscore_outliers(DATA) == []

    def test_a_loose_threshold_catches_it(self):
        assert zscore_outliers(DATA, threshold=2.0) == [6]

    def test_zero_spread_is_refused(self):
        with pytest.raises(Invalid) as caught:
            zscore_outliers([5.0, 5.0, 5.0])
        assert "not a verdict" in str(caught.value)


class TestZScoreOf:
    def test_the_score_of_a_value(self):
        assert zscore_of(100.0, DATA) == pytest.approx(
            2.449, abs=0.001
        )

    def test_the_mean_scores_zero(self):
        assert zscore_of(3.0, [1.0, 3.0, 5.0]) == 0.0
