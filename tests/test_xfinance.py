from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.xfinance import mirr, xirr, xnpv


class TestXnpv:
    def test_a_year_apart_discounts_once(self):
        assert xnpv(
            0.10, [-1000.0, 1100.0], [0, 365]
        ) == pytest.approx(0.0, abs=1e-6)

    def test_mismatched_lengths_are_refused(self):
        with pytest.raises(Invalid) as caught:
            xnpv(0.1, [-1000.0, 500.0], [0])
        assert "no place on the timeline" in str(
            caught.value
        )

    def test_out_of_order_dates_are_refused(self):
        with pytest.raises(Invalid) as caught:
            xnpv(0.1, [-1.0, 1.0], [365, 0])
        assert "non-decreasing" in str(caught.value)


class TestXirr:
    def test_it_recovers_a_simple_rate(self):
        assert xirr(
            [-1000.0, 1100.0], [0, 365]
        ) == pytest.approx(0.10, abs=1e-5)

    def test_an_uneven_schedule(self):
        rate = xirr([-1000.0, 500.0, 700.0], [0, 180, 400])
        # Re-discounting at the found rate should zero XNPV.
        assert xnpv(
            rate, [-1000.0, 500.0, 700.0], [0, 180, 400]
        ) == pytest.approx(0.0, abs=1e-4)

    def test_one_signed_flows_have_no_rate(self):
        with pytest.raises(Invalid) as caught:
            xirr([100.0, 200.0], [0, 365])
        assert "no internal rate" in str(caught.value)


class TestMirr:
    def test_it_returns_a_modified_rate(self):
        rate = mirr(
            [-1000.0, 300.0, 400.0, 500.0], 0.10, 0.12
        )
        assert 0.0 < rate < 0.2

    def test_one_sign_alone_is_refused(self):
        with pytest.raises(Invalid) as caught:
            mirr([100.0, 200.0], 0.1, 0.1)
        assert "both an outflow and an inflow" in str(
            caught.value
        )

    def test_too_few_flows_are_refused(self):
        with pytest.raises(Invalid):
            mirr([-1000.0], 0.1, 0.1)
