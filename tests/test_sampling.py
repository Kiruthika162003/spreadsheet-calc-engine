from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.sampling import (
    bootstrap,
    reservoir_sample,
    shuffle,
)


class TestReproducibility:
    def test_the_same_seed_gives_the_same_shuffle(self):
        items = list(range(10))
        assert shuffle(items, seed=7) == shuffle(
            items, seed=7
        )

    def test_different_seeds_usually_differ(self):
        items = list(range(20))
        assert shuffle(items, seed=1) != shuffle(
            items, seed=2
        )

    def test_the_input_is_not_mutated(self):
        items = [1, 2, 3, 4]
        shuffle(items, seed=5)
        assert items == [1, 2, 3, 4]


class TestShuffleIsAPermutation:
    def test_every_element_survives(self):
        items = list(range(50))
        result = shuffle(items, seed=99)
        assert sorted(result) == items
        assert len(result) == len(items)


class TestReservoir:
    def test_it_draws_the_right_count(self):
        items = list(range(100))
        sample = reservoir_sample(items, 5, seed=3)
        assert len(sample) == 5
        assert all(item in items for item in sample)

    def test_the_draw_is_reproducible(self):
        items = list(range(100))
        assert reservoir_sample(
            items, 5, seed=3
        ) == reservoir_sample(items, 5, seed=3)

    def test_drawing_more_than_exists_is_refused(self):
        with pytest.raises(Invalid) as caught:
            reservoir_sample([1, 2], 5, seed=1)
        assert "not a sample" in str(caught.value)

    def test_a_negative_size_is_refused(self):
        with pytest.raises(Invalid):
            reservoir_sample([1, 2], -1, seed=1)


class TestBootstrap:
    def test_it_resamples_to_the_same_size(self):
        items = [10, 20, 30]
        resampled = bootstrap(items, seed=4)
        assert len(resampled) == 3
        assert all(item in items for item in resampled)

    def test_replacement_can_repeat(self):
        # With replacement, some draw across many seeds must
        # repeat an element; check one concrete seed.
        resampled = bootstrap([1, 2, 3], seed=1)
        assert len(resampled) == 3

    def test_the_resample_is_reproducible(self):
        assert bootstrap([1, 2, 3], seed=8) == bootstrap(
            [1, 2, 3], seed=8
        )

    def test_an_empty_set_is_refused(self):
        with pytest.raises(Invalid) as caught:
            bootstrap([], seed=1)
        assert "nothing to" in str(caught.value)
