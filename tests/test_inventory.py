from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.inventory import fifo, lifo, weighted_average

EVENTS = [
    ("buy", 10.0, 2.0),
    ("buy", 10.0, 3.0),
    ("sell", 15.0, 0.0),
]


class TestTheMethodsDisagree:
    def test_fifo_expenses_the_old_layer(self):
        result = fifo(EVENTS)
        assert result.cogs == 35.0
        assert result.ending_value == 15.0

    def test_lifo_expenses_the_new_layer(self):
        result = lifo(EVENTS)
        assert result.cogs == 40.0
        assert result.ending_value == 10.0

    def test_weighted_average_blends(self):
        result = weighted_average(EVENTS)
        assert result.cogs == 37.5
        assert result.ending_value == 12.5

    def test_fifo_lifo_average_order(self):
        # In a rising market FIFO reports the lowest COGS,
        # LIFO the highest, average between.
        assert (
            fifo(EVENTS).cogs
            < weighted_average(EVENTS).cogs
            < lifo(EVENTS).cogs
        )


class TestReconciliation:
    @pytest.mark.parametrize(
        "method", [fifo, lifo, weighted_average]
    )
    def test_cogs_plus_ending_is_total_purchases(self, method):
        result = method(EVENTS)
        assert result.cogs + result.ending_value == 50.0
        assert result.ending_units == 5.0


class TestOverselling:
    def test_fifo_refuses_to_oversell(self):
        with pytest.raises(Invalid) as caught:
            fifo([("buy", 5.0, 1.0), ("sell", 10.0, 0.0)])
        assert "oversells" in str(caught.value)

    def test_average_refuses_to_oversell(self):
        with pytest.raises(Invalid) as caught:
            weighted_average(
                [("buy", 5.0, 1.0), ("sell", 6.0, 0.0)]
            )
        assert "cannot go negative" in str(caught.value)
