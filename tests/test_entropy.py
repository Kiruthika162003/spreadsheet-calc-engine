from __future__ import annotations

import pytest

from gridiron.entropy import (
    entropy,
    gini,
    normalized_entropy,
)
from gridiron.errors import Invalid


class TestEntropy:
    def test_a_fair_coin_is_one_bit(self):
        assert entropy([1, 1]) == pytest.approx(1.0)

    def test_a_pure_set_is_zero(self):
        assert entropy([5, 0, 0]) == pytest.approx(0.0)

    def test_a_four_way_even_split_is_two_bits(self):
        assert entropy([1, 1, 1, 1]) == pytest.approx(2.0)

    def test_a_zero_count_term_is_not_infinite(self):
        # The empty category contributes zero, not -inf.
        assert entropy([3, 0]) == pytest.approx(0.0)


class TestGini:
    def test_a_fair_coin(self):
        assert gini([1, 1]) == pytest.approx(0.5)

    def test_a_pure_set(self):
        assert gini([5, 0]) == pytest.approx(0.0)

    def test_it_tracks_entropy_direction(self):
        # More mixed means both entropy and gini rise.
        assert gini([1, 1, 1, 1]) > gini([3, 1])
        assert entropy([1, 1, 1, 1]) > entropy([3, 1])


class TestNormalized:
    def test_an_even_split_normalizes_to_one(self):
        assert normalized_entropy([1, 1, 1, 1]) == (
            pytest.approx(1.0)
        )

    def test_a_pure_set_normalizes_to_zero(self):
        assert normalized_entropy([5, 0]) == 0.0


class TestRefusals:
    def test_a_zero_total_is_refused(self):
        with pytest.raises(Invalid) as caught:
            entropy([0, 0])
        assert "over nothing" in str(caught.value)

    def test_a_negative_count_is_refused(self):
        with pytest.raises(Invalid):
            gini([3, -1])
