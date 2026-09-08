from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.rankcorr import kendall_tau, spearman

X = [1.0, 2.0, 3.0, 4.0, 5.0]
CURVE = [1.0, 4.0, 9.0, 16.0, 25.0]


class TestSpearman:
    def test_a_monotone_curve_scores_one(self):
        # Nonlinear but perfectly monotone: rho is 1 where
        # Pearson would be below it.
        assert spearman(X, CURVE) == pytest.approx(1.0)

    def test_a_perfect_inverse_is_minus_one(self):
        assert spearman(
            X, list(reversed(CURVE))
        ) == pytest.approx(-1.0)

    def test_ties_use_average_ranks(self):
        a = [1.0, 2.0, 2.0, 3.0]
        b = [1.0, 2.0, 3.0, 4.0]
        assert spearman(a, b) == pytest.approx(
            0.9487, abs=1e-4
        )

    def test_mismatched_lengths_are_refused(self):
        with pytest.raises(Invalid) as caught:
            spearman([1.0, 2.0], [1.0])
        assert "must pair" in str(caught.value)


class TestKendall:
    def test_a_monotone_relation_scores_one(self):
        assert kendall_tau(X, CURVE) == pytest.approx(1.0)

    def test_a_perfect_inverse(self):
        assert kendall_tau(
            X, list(reversed(CURVE))
        ) == pytest.approx(-1.0)

    def test_it_stays_in_range(self):
        a = [3.0, 1.0, 4.0, 1.0, 5.0]
        b = [2.0, 7.0, 1.0, 8.0, 2.0]
        assert -1.0 <= kendall_tau(a, b) <= 1.0


class TestRefusals:
    def test_no_variance_is_refused(self):
        with pytest.raises(Invalid) as caught:
            spearman([5.0, 5.0, 5.0], [1.0, 2.0, 3.0])
        assert "nothing to rank against" in str(caught.value)

    def test_too_few_observations(self):
        with pytest.raises(Invalid):
            kendall_tau([1.0], [2.0])
