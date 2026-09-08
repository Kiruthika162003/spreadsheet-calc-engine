"""Bit sets: membership packed into an integer, with the set operations that follow.

A set of small non-negative integers, the row numbers a
filter selected, the days a resource is booked, packs into a
single integer where bit i is set when i is a member, and the
set operations become bitwise ones: union is or, intersection
is and, difference is and-not. This is the representation
that makes those operations fast, and the module wraps it so
a caller works in members rather than remembering which bit
is which. The one edge that a raw bitmask fumbles is the
negative index: bit minus one has no meaning, so adding a
negative member is refused rather than silently wrapping to a
high bit through Python's two's-complement integers, which
would put a phantom member in the set and corrupt every count
and iteration after. Membership, add, and remove are exact,
removing an absent member is a no-op rather than an error
because a set does not care whether you asked it to remove
something twice, and the count is the population count of the
underlying integer, the number of set bits, which Python
gives exactly rather than the float an approximate popcount
would risk. Iterating yields members in ascending order
regardless of insertion order, because a set has no order and
imposing the natural one keeps a serialized set reproducible
rather than dependent on the sequence of adds.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid


@dataclass
class BitSet:
    bits: int = field(default=0)

    @classmethod
    def of(cls, members: list[int]) -> BitSet:
        result = cls()
        for member in members:
            result.add(member)
        return result

    def add(self, member: int) -> None:
        if member < 0:
            raise Invalid(
                f"{member} is negative; a bit set holds "
                "non-negative members and a negative would "
                "wrap to a phantom high bit"
            )
        self.bits |= 1 << member

    def remove(self, member: int) -> None:
        if member < 0:
            raise Invalid("members are non-negative")
        self.bits &= ~(1 << member)

    def contains(self, member: int) -> bool:
        if member < 0:
            return False
        return bool(self.bits & (1 << member))

    def count(self) -> int:
        return self.bits.bit_count()

    def members(self) -> list[int]:
        result = []
        remaining = self.bits
        index = 0
        while remaining:
            if remaining & 1:
                result.append(index)
            remaining >>= 1
            index += 1
        return result

    def union(self, other: BitSet) -> BitSet:
        return BitSet(bits=self.bits | other.bits)

    def intersection(self, other: BitSet) -> BitSet:
        return BitSet(bits=self.bits & other.bits)

    def difference(self, other: BitSet) -> BitSet:
        return BitSet(bits=self.bits & ~other.bits)
