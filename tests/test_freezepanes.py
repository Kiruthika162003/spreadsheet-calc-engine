from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.freezepanes import FreezeView


class TestVisibleRows:
    def test_no_freeze_is_a_plain_window(self):
        view = FreezeView(
            total_rows=100,
            total_cols=10,
            viewport_rows=5,
            viewport_cols=5,
        )
        assert view.visible_rows(0) == [0, 1, 2, 3, 4]
        assert view.visible_rows(3) == [3, 4, 5, 6, 7]

    def test_frozen_rows_stay_while_body_scrolls(self):
        view = FreezeView(
            total_rows=100,
            total_cols=10,
            frozen_rows=2,
            viewport_rows=5,
        )
        # Frozen rows 0,1 always; body window of 3 rows.
        assert view.visible_rows(0) == [0, 1, 2, 3, 4]
        # Scrolling one body row shows sheet row 3 first in
        # the body, not row 1 again.
        assert view.visible_rows(1) == [0, 1, 3, 4, 5]

    def test_the_offset_counts_body_rows(self):
        view = FreezeView(
            total_rows=100,
            total_cols=10,
            frozen_rows=2,
            viewport_rows=5,
        )
        assert view.visible_rows(5) == [0, 1, 7, 8, 9]


class TestClamping:
    def test_scrolling_past_the_end_clamps(self):
        view = FreezeView(
            total_rows=6,
            total_cols=10,
            frozen_rows=1,
            viewport_rows=4,
        )
        # Body is rows 1..5 (5 rows), window 3, last window
        # starts at row 3.
        far = view.visible_rows(1000)
        assert far == [0, 3, 4, 5]

    def test_no_scrolling_into_the_void(self):
        view = FreezeView(
            total_rows=4,
            total_cols=10,
            viewport_rows=10,
            viewport_cols=5,
        )
        # Only 4 rows exist; the window never exceeds them.
        assert view.visible_rows(0) == [0, 1, 2, 3]
        assert view.visible_rows(50) == [0, 1, 2, 3]


class TestColumns:
    def test_frozen_columns_stay(self):
        view = FreezeView(
            total_rows=10,
            total_cols=20,
            frozen_cols=1,
            viewport_cols=4,
        )
        assert view.visible_cols(0) == [0, 1, 2, 3]
        assert view.visible_cols(2) == [0, 3, 4, 5]


class TestRefusals:
    def test_a_band_taller_than_the_viewport(self):
        with pytest.raises(Invalid) as caught:
            FreezeView(
                total_rows=100,
                total_cols=10,
                frozen_rows=5,
                viewport_rows=5,
            )
        assert "no room for the body" in str(caught.value)

    def test_a_negative_band(self):
        with pytest.raises(Invalid) as caught:
            FreezeView(
                total_rows=10,
                total_cols=10,
                frozen_rows=-1,
            )
        assert "cannot be negative" in str(caught.value)
