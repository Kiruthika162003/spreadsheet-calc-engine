from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.probdist import (
    binomial_cdf,
    binomial_pmf,
    poisson_cdf,
    poisson_pmf,
)


class TestBinomial:
    def test_the_textbook_case(self):
        # 2 heads in 5 fair flips: C(5,2)/32 = 10/32.
        assert binomial_pmf(2, 5, 0.5) == pytest.approx(
            0.3125
        )

    def test_the_pmf_sums_to_one(self):
        total = sum(
            binomial_pmf(k, 5, 0.3) for k in range(6)
        )
        assert total == pytest.approx(1.0)

    def test_more_successes_than_trials_is_impossible(self):
        assert binomial_pmf(6, 5, 0.5) == 0.0

    def test_it_survives_large_counts(self):
        # No overflow computing in log space.
        assert binomial_pmf(100, 1000, 0.1) == (
            pytest.approx(0.042, abs=0.001)
        )

    def test_the_cdf_reaches_one(self):
        assert binomial_cdf(5, 5, 0.5) == pytest.approx(1.0)

    def test_a_bad_probability_is_refused(self):
        with pytest.raises(Invalid):
            binomial_pmf(1, 5, 1.5)


class TestPoisson:
    def test_the_textbook_case(self):
        # k=3, lambda=2: e^-2 * 8 / 6.
        assert poisson_pmf(3, 2.0) == pytest.approx(
            0.180447, abs=1e-6
        )

    def test_the_pmf_sums_to_one(self):
        total = sum(poisson_pmf(k, 3.0) for k in range(40))
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_a_rate_of_zero_is_all_mass_at_zero(self):
        assert poisson_pmf(0, 0.0) == 1.0
        assert poisson_pmf(1, 0.0) == 0.0

    def test_the_cdf_reaches_one(self):
        assert poisson_cdf(1000, 2.0) == pytest.approx(1.0)

    def test_a_negative_rate_is_refused(self):
        with pytest.raises(Invalid):
            poisson_pmf(1, -1.0)
