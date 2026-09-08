from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.financeratios import (
    break_even,
    cagr,
    payback_period,
    roi,
)


class TestCagr:
    def test_doubling_over_ten_years(self):
        assert cagr(100.0, 200.0, 10.0) == pytest.approx(
            2 ** 0.1 - 1
        )

    def test_a_nonpositive_value_is_a_complex_root(self):
        with pytest.raises(Invalid) as caught:
            cagr(-100.0, 200.0, 10.0)
        assert "complex root" in str(caught.value)

    def test_zero_years_is_refused(self):
        with pytest.raises(Invalid):
            cagr(100.0, 200.0, 0.0)


class TestRoi:
    def test_a_fifty_percent_return(self):
        assert roi(150.0, 100.0) == 0.5

    def test_a_loss_is_negative(self):
        assert roi(80.0, 100.0) == pytest.approx(-0.2)

    def test_zero_cost_is_refused(self):
        with pytest.raises(Invalid) as caught:
            roi(100.0, 0.0)
        assert "diligence early" in str(caught.value)


class TestPayback:
    def test_it_interpolates_within_the_period(self):
        assert (
            payback_period([-1000.0, 400.0, 400.0, 400.0])
            == 2.5
        )

    def test_a_project_that_never_recovers(self):
        assert (
            payback_period([-1000.0, 100.0, 100.0]) is None
        )

    def test_an_immediate_positive_start(self):
        assert payback_period([500.0, -100.0]) == 0.0


class TestBreakEven:
    def test_fixed_over_margin(self):
        assert break_even(1000.0, 10.0, 6.0) == 250.0

    def test_a_nonpositive_margin_never_breaks_even(self):
        with pytest.raises(Invalid) as caught:
            break_even(1000.0, 5.0, 6.0)
        assert "never breaks even" in str(caught.value)

    def test_a_negative_fixed_cost_is_refused(self):
        with pytest.raises(Invalid):
            break_even(-100.0, 10.0, 6.0)
