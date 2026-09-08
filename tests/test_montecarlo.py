from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.montecarlo import simulate


def two_uniforms():
    return [(0.0, 1.0), (0.0, 1.0)]


class TestReproducibility:
    def test_the_same_seed_gives_the_same_estimate(self):
        a = simulate(
            lambda s: s[0] + s[1], two_uniforms(), 2000, 42
        )
        b = simulate(
            lambda s: s[0] + s[1], two_uniforms(), 2000, 42
        )
        assert a.mean == b.mean
        assert a.percentiles == b.percentiles

    def test_different_seeds_differ(self):
        a = simulate(
            lambda s: s[0] + s[1], two_uniforms(), 2000, 1
        )
        b = simulate(
            lambda s: s[0] + s[1], two_uniforms(), 2000, 2
        )
        assert a.mean != b.mean


class TestEstimate:
    def test_the_mean_of_two_uniforms(self):
        result = simulate(
            lambda s: s[0] + s[1], two_uniforms(), 5000, 42
        )
        assert result.mean == pytest.approx(1.0, abs=0.05)

    def test_the_band_brackets_the_median(self):
        result = simulate(
            lambda s: s[0] + s[1], two_uniforms(), 5000, 42
        )
        p = result.percentiles
        assert p[5] < p[50] < p[95]

    def test_outcomes_stay_in_range(self):
        result = simulate(
            lambda s: s[0], [(10.0, 20.0)], 1000, 7
        )
        assert result.minimum >= 10.0
        assert result.maximum <= 20.0


class TestRefusals:
    def test_zero_trials_is_refused(self):
        with pytest.raises(Invalid):
            simulate(lambda s: s[0], [(0.0, 1.0)], 0, 1)

    def test_a_backward_range_is_refused(self):
        with pytest.raises(Invalid) as caught:
            simulate(lambda s: s[0], [(5.0, 1.0)], 100, 1)
        assert "samples nothing" in str(caught.value)

    def test_a_model_error_surfaces(self):
        with pytest.raises(ZeroDivisionError):
            simulate(
                lambda _s: 1 / 0, [(0.0, 1.0)], 10, 1
            )
