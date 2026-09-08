from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.waterfall import build_waterfall, ending_total


class TestBridging:
    def test_bars_float_between_running_totals(self):
        bars = build_waterfall(
            100.0,
            [("sales", 50.0), ("costs", -30.0)],
        )
        # start, sales, costs, end.
        assert bars[0].kind == "total"
        assert bars[1].base == 100.0
        assert bars[1].top == 150.0
        assert bars[2].base == 150.0
        assert bars[2].top == 120.0
        assert ending_total(bars) == 120.0

    def test_direction_travels_with_the_bar(self):
        bars = build_waterfall(
            100.0, [("up", 20.0), ("down", -5.0)]
        )
        assert bars[1].direction() == "up"
        assert bars[2].direction() == "down"

    def test_totals_are_anchored_not_floating(self):
        bars = build_waterfall(100.0, [("x", 10.0)])
        assert bars[0].base == 0.0
        assert bars[-1].base == 0.0
        assert bars[0].direction() == "total"


class TestReconciliation:
    def test_a_matching_declared_end_passes(self):
        bars = build_waterfall(
            100.0,
            [("a", 50.0), ("b", -20.0)],
            declared_end=130.0,
        )
        assert ending_total(bars) == 130.0

    def test_a_mismatched_declared_end_is_refused(self):
        with pytest.raises(Invalid) as caught:
            build_waterfall(
                100.0,
                [("a", 50.0)],
                declared_end=999.0,
            )
        assert "do not reconcile" in str(caught.value)


class TestZeroSteps:
    def test_a_zero_delta_is_kept_as_a_flat_marker(self):
        bars = build_waterfall(
            100.0, [("nochange", 0.0), ("up", 10.0)]
        )
        assert bars[1].base == bars[1].top == 100.0
        assert bars[1].height() == 0.0
        assert len(bars) == 4

    def test_the_heights_are_absolute(self):
        bars = build_waterfall(100.0, [("drop", -40.0)])
        assert bars[1].height() == 40.0
