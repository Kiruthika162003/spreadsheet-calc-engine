from __future__ import annotations

import pytest

from gridiron.allocate import allocate
from gridiron.errors import Invalid


class TestAllocation:
    def test_the_parts_sum_to_the_whole(self):
        parts = allocate(100, [1.0, 1.0, 1.0])
        assert sum(parts) == 100

    def test_the_leftover_unit_goes_to_the_largest_remainder(self):
        # 100/3 is 33.33 each; the extra unit lands on the
        # first share, ties broken toward the earlier.
        assert allocate(100, [1.0, 1.0, 1.0]) == [34, 33, 33]

    def test_seats_by_vote_share(self):
        assert allocate(100, [47.0, 43.0, 10.0]) == [
            47,
            43,
            10,
        ]

    def test_unequal_weights(self):
        parts = allocate(10, [3.0, 1.0])
        assert sum(parts) == 10
        assert parts[0] > parts[1]

    def test_a_zero_whole_gives_zeros(self):
        assert allocate(0, [1.0, 2.0, 3.0]) == [0, 0, 0]


class TestTheSumLaw:
    def test_it_always_sums(self):
        cases = [
            (7, [1.0, 1.0, 1.0]),
            (50, [0.1, 0.2, 0.7]),
            (13, [5.0, 5.0, 5.0, 5.0]),
            (1, [1.0, 1.0]),
        ]
        for whole, weights in cases:
            assert sum(allocate(whole, weights)) == whole


class TestRefusals:
    def test_a_negative_whole(self):
        with pytest.raises(Invalid):
            allocate(-1, [1.0])

    def test_zero_total_weight(self):
        with pytest.raises(Invalid) as caught:
            allocate(10, [0.0, 0.0])
        assert "by no weight is undefined" in str(
            caught.value
        )

    def test_a_negative_weight(self):
        with pytest.raises(Invalid) as caught:
            allocate(10, [2.0, -1.0])
        assert "negative share" in str(caught.value)
