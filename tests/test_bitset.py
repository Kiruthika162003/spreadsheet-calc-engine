from __future__ import annotations

import pytest

from gridiron.bitset import BitSet
from gridiron.errors import Invalid


class TestMembership:
    def test_add_and_contains(self):
        s = BitSet.of([1, 3, 5])
        assert s.contains(3)
        assert not s.contains(2)

    def test_members_come_back_sorted(self):
        s = BitSet.of([5, 1, 3])
        assert s.members() == [1, 3, 5]

    def test_the_count_is_the_population(self):
        assert BitSet.of([1, 3, 5, 7]).count() == 4

    def test_removing_an_absent_member_is_a_noop(self):
        s = BitSet.of([1, 2])
        s.remove(9)
        assert s.members() == [1, 2]


class TestSetOperations:
    def test_union(self):
        a = BitSet.of([1, 3, 5])
        b = BitSet.of([3, 4])
        assert a.union(b).members() == [1, 3, 4, 5]

    def test_intersection(self):
        a = BitSet.of([1, 3, 5])
        b = BitSet.of([3, 5, 9])
        assert a.intersection(b).members() == [3, 5]

    def test_difference(self):
        a = BitSet.of([1, 3, 5])
        b = BitSet.of([3])
        assert a.difference(b).members() == [1, 5]


class TestRefusals:
    def test_a_negative_member_is_refused(self):
        s = BitSet()
        with pytest.raises(Invalid) as caught:
            s.add(-1)
        assert "phantom high bit" in str(caught.value)

    def test_a_negative_is_never_a_member(self):
        assert BitSet.of([0, 1]).contains(-1) is False
