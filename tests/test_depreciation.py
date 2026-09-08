from __future__ import annotations

import pytest

from gridiron.depreciation import (
    double_declining,
    straight_line,
    sum_of_years_digits,
    total_depreciation,
)
from gridiron.errors import Invalid

METHODS = [
    straight_line,
    double_declining,
    sum_of_years_digits,
]


class TestTheSalvageLaw:
    @pytest.mark.parametrize("method", METHODS)
    def test_the_book_value_lands_on_salvage(self, method):
        rows = method(1000.0, 100.0, 5)
        assert rows[-1].book_value == pytest.approx(100.0)

    @pytest.mark.parametrize("method", METHODS)
    def test_total_equals_the_depreciable_base(self, method):
        rows = method(1000.0, 100.0, 5)
        assert total_depreciation(rows) == pytest.approx(
            900.0
        )

    @pytest.mark.parametrize("method", METHODS)
    def test_one_row_per_period(self, method):
        rows = method(1000.0, 100.0, 5)
        assert len(rows) == 5
        assert [r.period for r in rows] == [1, 2, 3, 4, 5]


class TestMethodShapes:
    def test_straight_line_is_flat(self):
        rows = straight_line(1000.0, 100.0, 5)
        charges = {r.depreciation for r in rows}
        assert charges == {180.0}

    def test_double_declining_front_loads(self):
        rows = double_declining(1000.0, 100.0, 5)
        assert rows[0].depreciation > rows[-1].depreciation

    def test_syd_also_front_loads(self):
        rows = sum_of_years_digits(1000.0, 100.0, 5)
        assert rows[0].depreciation > rows[1].depreciation


class TestRefusals:
    def test_salvage_above_cost_is_refused(self):
        with pytest.raises(Invalid) as caught:
            straight_line(100.0, 200.0, 5)
        assert "appreciates" in str(caught.value)

    def test_a_zero_life_is_refused(self):
        with pytest.raises(Invalid):
            straight_line(1000.0, 100.0, 0)

    def test_negative_salvage_is_refused(self):
        with pytest.raises(Invalid):
            straight_line(1000.0, -50.0, 5)
