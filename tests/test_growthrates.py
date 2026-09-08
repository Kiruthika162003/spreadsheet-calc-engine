from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.growthrates import (
    average_growth,
    cagr,
    period_rates,
    total_growth,
)


class TestPeriodRates:
    def test_the_step_changes(self):
        assert period_rates([100.0, 150.0, 75.0]) == [
            pytest.approx(0.5),
            pytest.approx(-0.5),
        ]

    def test_growth_from_zero_is_absent(self):
        assert period_rates([0.0, 50.0]) == [None]

    def test_too_few_values_are_refused(self):
        with pytest.raises(Invalid):
            period_rates([5.0])


class TestTheGeometricAverage:
    def test_it_is_not_the_arithmetic_mean(self):
        # +50% then -50% averages to zero arithmetically but
        # the money is down, so the geometric average is
        # negative.
        assert average_growth([100.0, 150.0, 75.0]) < 0

    def test_it_compounds_back_to_the_endpoint(self):
        values = [100.0, 150.0, 75.0]
        g = average_growth(values)
        periods = len(values) - 1
        assert values[0] * (1 + g) ** periods == (
            pytest.approx(values[-1])
        )

    def test_a_steady_series_recovers_its_rate(self):
        # 10% per period for three periods.
        values = [100.0, 110.0, 121.0, 133.1]
        assert cagr(values) == pytest.approx(0.10)


class TestTotalGrowth:
    def test_end_over_start(self):
        assert total_growth([100.0, 75.0]) == -0.25


class TestRefusals:
    def test_cagr_needs_positive_endpoints(self):
        with pytest.raises(Invalid) as caught:
            cagr([-100.0, 200.0])
        assert "crosses zero" in str(caught.value)

    def test_total_growth_from_zero_is_undefined(self):
        with pytest.raises(Invalid):
            total_growth([0.0, 50.0])
