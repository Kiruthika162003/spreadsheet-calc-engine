from __future__ import annotations

import pytest

from gridiron.distributions import (
    normal_cdf,
    normal_inv,
    normal_pdf,
    standard_cdf,
    standard_inv,
)
from gridiron.errors import Invalid


class TestPdf:
    def test_the_peak_at_the_mean(self):
        assert normal_pdf(0.0) == pytest.approx(
            0.39894, abs=1e-5
        )

    def test_it_is_symmetric(self):
        assert normal_pdf(-1.5) == pytest.approx(
            normal_pdf(1.5)
        )

    def test_a_nonpositive_sd_is_a_spike(self):
        with pytest.raises(Invalid) as caught:
            normal_pdf(0.0, sd=0.0)
        assert "no finite density" in str(caught.value)


class TestCdf:
    def test_the_median_is_a_half(self):
        assert standard_cdf(0.0) == pytest.approx(0.5)

    def test_the_famous_ninety_seven_point_five(self):
        assert standard_cdf(1.96) == pytest.approx(
            0.975, abs=1e-4
        )

    def test_the_tails_are_correct_not_just_the_middle(self):
        # Three sigma is about 0.99865.
        assert standard_cdf(3.0) == pytest.approx(
            0.99865, abs=1e-4
        )

    def test_a_shifted_scaled_normal(self):
        assert normal_cdf(
            110.0, mean=100.0, sd=10.0
        ) == pytest.approx(standard_cdf(1.0))


class TestInverse:
    def test_the_quantile_inverts_the_cdf(self):
        assert standard_inv(0.975) == pytest.approx(
            1.96, abs=1e-3
        )

    def test_the_round_trip_holds(self):
        for p in (0.1, 0.3, 0.5, 0.8, 0.99):
            z = standard_inv(p)
            assert standard_cdf(z) == pytest.approx(
                p, abs=1e-6
            )

    def test_a_probability_at_the_edge_is_infinite(self):
        with pytest.raises(Invalid) as caught:
            standard_inv(0.0)
        assert "infinite" in str(caught.value)

    def test_a_probability_over_one_is_refused(self):
        with pytest.raises(Invalid):
            standard_inv(1.5)

    def test_the_inverse_carries_mean_and_sd(self):
        q = normal_inv(0.5, mean=50.0, sd=5.0)
        assert q == pytest.approx(50.0, abs=1e-3)
