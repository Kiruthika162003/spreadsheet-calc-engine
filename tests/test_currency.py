from __future__ import annotations

import pytest

from gridiron.currency import RateTable
from gridiron.errors import Invalid


def table() -> RateTable:
    return RateTable(
        base="USD", rates={"EUR": 0.9, "GBP": 0.8}
    )


class TestConversion:
    def test_base_to_currency(self):
        assert table().convert(100.0, "USD", "EUR") == 90.0

    def test_currency_to_base(self):
        assert table().convert(90.0, "EUR", "USD") == 100.0

    def test_a_cross_rate_triangulates(self):
        assert table().cross_rate("EUR", "GBP") == (
            pytest.approx(0.8 / 0.9)
        )

    def test_the_base_rate_is_one(self):
        assert table().convert(50.0, "USD", "USD") == 50.0

    def test_case_is_folded(self):
        assert table().convert(100.0, "usd", "eur") == 90.0


class TestRoundTrip:
    def test_there_and_back(self):
        t = table()
        for pair in (("GBP", "EUR"), ("USD", "GBP")):
            here = t.convert(250.0, *pair)
            back = t.convert(here, pair[1], pair[0])
            assert back == pytest.approx(250.0)


class TestRefusals:
    def test_an_unknown_currency_is_refused(self):
        with pytest.raises(Invalid) as caught:
            table().convert(1.0, "JPY", "USD")
        assert "at par is almost never right" in str(
            caught.value
        )

    def test_a_nonpositive_rate_is_refused(self):
        t = table()
        with pytest.raises(Invalid) as caught:
            t.set_rate("CAD", 0.0)
        assert "rates are positive" in str(caught.value)

    def test_the_base_rate_cannot_be_reset(self):
        with pytest.raises(Invalid) as caught:
            table().set_rate("USD", 2.0)
        assert "one by definition" in str(caught.value)

    def test_adding_a_currency_needs_one_rate(self):
        t = table()
        t.set_rate("CAD", 1.3)
        assert t.convert(13.0, "CAD", "USD") == (
            pytest.approx(10.0)
        )
