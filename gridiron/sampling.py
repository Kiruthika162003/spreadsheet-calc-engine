"""Sampling: randomness with a seed, because a report must reproduce.

Random sampling in a spreadsheet has a hidden requirement
that the word random hides: the result must be reproducible,
because a sample that changes every recalculation is a sample
nobody can audit, cite, or defend in a meeting. So every
operation here takes a seed and derives its randomness from
the same linear congruential generator the volatile module
uses, which means the same seed and the same data always
produce the same sample, and a reviewer can rerun the exact
draw. The shuffle is Fisher-Yates, the only shuffle that is
uniform over permutations, because the naive sort-by-random
shuffle is subtly biased and the bias is invisible until a
statistician looks. Reservoir sampling draws k items in one
pass without knowing the length in advance, which matters for
the streaming case and is correct for the in-memory one too,
and it refuses to draw more items than exist rather than
returning the whole set and calling it a sample of a larger
number. The bootstrap resamples with replacement to the same
size, the technique that underlies confidence intervals, and
it is kept distinct from sampling without replacement because
conflating them is how a variance estimate comes out wrong by
a factor nobody can find.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid

_MODULUS = 2147483647
_MULTIPLIER = 48271


@dataclass
class SeededGenerator:
    seed: int
    _state: int = field(init=False)

    def __post_init__(self) -> None:
        self._state = self.seed % _MODULUS or 1

    def next_int(self, bound: int) -> int:
        if bound < 1:
            raise Invalid("a bound must be positive")
        self._state = (
            self._state * _MULTIPLIER
        ) % _MODULUS
        return self._state % bound


def shuffle(items: list, seed: int) -> list:
    generator = SeededGenerator(seed=seed)
    result = list(items)
    for index in range(len(result) - 1, 0, -1):
        swap = generator.next_int(index + 1)
        result[index], result[swap] = (
            result[swap],
            result[index],
        )
    return result


def reservoir_sample(
    items: list, k: int, seed: int
) -> list:
    if k < 0:
        raise Invalid("a sample size cannot be negative")
    if k > len(items):
        raise Invalid(
            f"cannot draw {k} from {len(items)}; a sample "
            "of more than exists is not a sample"
        )
    generator = SeededGenerator(seed=seed)
    reservoir = list(items[:k])
    for index in range(k, len(items)):
        pick = generator.next_int(index + 1)
        if pick < k:
            reservoir[pick] = items[index]
    return reservoir


def bootstrap(items: list, seed: int) -> list:
    if not items:
        raise Invalid(
            "a bootstrap of an empty set has nothing to "
            "resample"
        )
    generator = SeededGenerator(seed=seed)
    return [
        items[generator.next_int(len(items))]
        for _ in range(len(items))
    ]
