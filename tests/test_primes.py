from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.primes import (
    is_prime,
    next_prime,
    prime_factors,
    product_of,
)


class TestIsPrime:
    def test_the_small_primes(self):
        assert [n for n in range(20) if is_prime(n)] == [
            2, 3, 5, 7, 11, 13, 17, 19,
        ]

    def test_one_and_below_are_not_prime(self):
        assert is_prime(1) is False
        assert is_prime(0) is False
        assert is_prime(-7) is False

    def test_a_large_prime(self):
        assert is_prime(7919) is True
        assert is_prime(7920) is False


class TestFactorization:
    def test_multiplicities_are_grouped(self):
        assert prime_factors(360) == [(2, 3), (3, 2), (5, 1)]

    def test_a_prime_factors_to_itself(self):
        assert prime_factors(17) == [(17, 1)]

    def test_the_factors_multiply_back(self):
        for n in range(2, 200):
            assert product_of(prime_factors(n)) == n

    def test_factoring_below_two_is_refused(self):
        with pytest.raises(Invalid) as caught:
            prime_factors(1)
        assert "units or zero" in str(caught.value)


class TestNextPrime:
    def test_it_steps_to_the_next(self):
        assert next_prime(13) == 17
        assert next_prime(100) == 101

    def test_a_ceiling_bounds_the_search(self):
        with pytest.raises(Invalid) as caught:
            next_prime(20, ceiling=22)
        assert "search is finite" in str(caught.value)
