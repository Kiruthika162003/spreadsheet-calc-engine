"""Primes: testing, factoring, and stepping to the next one, honestly bounded.

Prime arithmetic wanders into a spreadsheet through
check-digit schemes and hashing, and the operations are
small but have edges that a naive version fumbles. Primality
testing trial-divides only up to the square root, because a
factor larger than the root implies a cofactor smaller than
it that would already have been found, and testing past the
root is work that can never change the answer. One is not
prime and neither is anything below it, a definition rather
than a special case, stated because the off-by-one at the
bottom of the number line is where prime code most often goes
wrong. Factorization returns the prime factors with their
multiplicities as ordered pairs, so twelve comes back as two
squared times three rather than a flat list a caller must
re-count, and the product of the factors returned equals the
input, an identity the tests check because a factorization
that does not multiply back is not a factorization. The next
prime steps upward from a number and is bounded by a stated
ceiling rather than searching forever, because while primes
are infinite a search is not, and a function that could hang
on a large input is worse than one that says it looked this
far and stopped. Negative inputs and zero are refused for
factorization, because the fundamental theorem of arithmetic
is about positive integers and factoring a negative is a
question about units this module does not answer.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def prime_factors(n: int) -> list[tuple[int, int]]:
    if n < 2:
        raise Invalid(
            "factorization is about integers of two or "
            "more; the theorem does not speak of units or "
            "zero"
        )
    factors: list[tuple[int, int]] = []
    remaining = n
    divisor = 2
    while divisor * divisor <= remaining:
        if remaining % divisor == 0:
            power = 0
            while remaining % divisor == 0:
                remaining //= divisor
                power += 1
            factors.append((divisor, power))
        divisor += 1 if divisor == 2 else 2
    if remaining > 1:
        factors.append((remaining, 1))
    return factors


def next_prime(n: int, ceiling: int = 1_000_000) -> int:
    candidate = n + 1
    while candidate <= ceiling:
        if is_prime(candidate):
            return candidate
        candidate += 1
    raise Invalid(
        f"no prime found from {n + 1} up to the ceiling of "
        f"{ceiling}; a search is finite even though primes "
        "are not"
    )


def product_of(factors: list[tuple[int, int]]) -> int:
    result = 1
    for prime, power in factors:
        result *= prime**power
    return result
