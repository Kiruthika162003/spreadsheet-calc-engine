from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.rateconvert import (
    effective,
    effective_continuous,
    nominal,
    nominal_continuous,
)


class TestEffective:
    def test_monthly_compounding_earns_more(self):
        assert effective(0.05, 12) == pytest.approx(
            0.051162, abs=1e-6
        )

    def test_annual_compounding_is_the_nominal(self):
        assert effective(0.05, 1) == pytest.approx(0.05)

    def test_more_frequent_earns_more(self):
        assert effective(0.05, 12) > effective(0.05, 4)


class TestInverse:
    def test_nominal_inverts_effective(self):
        eff = effective(0.05, 12)
        assert nominal(eff, 12) == pytest.approx(0.05)

    def test_the_round_trip_across_frequencies(self):
        for periods in (1, 2, 4, 12, 365):
            eff = effective(0.08, periods)
            assert nominal(eff, periods) == pytest.approx(
                0.08
            )


class TestContinuous:
    def test_continuous_is_its_own_formula(self):
        assert effective_continuous(0.05) == pytest.approx(
            0.051271, abs=1e-6
        )

    def test_continuous_round_trip(self):
        assert nominal_continuous(
            effective_continuous(0.05)
        ) == pytest.approx(0.05)

    def test_continuous_exceeds_any_finite_frequency(self):
        assert effective_continuous(0.05) > effective(
            0.05, 365
        )


class TestRefusals:
    def test_a_zero_frequency_is_refused(self):
        with pytest.raises(Invalid) as caught:
            effective(0.05, 0)
        assert "positive whole number" in str(caught.value)

    def test_a_rate_below_minus_one_is_refused(self):
        with pytest.raises(Invalid):
            effective(-1.5, 12)
