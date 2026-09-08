from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.multisort import SortKey, multisort

RECORDS = [
    ["Eng", 100.0, "Ada"],
    ["Ops", 90.0, "Bob"],
    ["Eng", 120.0, "Cy"],
    ["Ops", 90.0, "Dot"],
]


class TestMultiKey:
    def test_dept_then_salary_descending(self):
        out = multisort(
            RECORDS, [SortKey(0), SortKey(1, descending=True)]
        )
        assert [r[2] for r in out] == [
            "Cy",
            "Ada",
            "Bob",
            "Dot",
        ]

    def test_ties_keep_arrival_order(self):
        out = multisort(
            RECORDS, [SortKey(0), SortKey(1, descending=True)]
        )
        # Bob and Dot tie on dept and salary; Bob came first.
        ops = [r[2] for r in out if r[0] == "Ops"]
        assert ops == ["Bob", "Dot"]

    def test_a_single_key(self):
        out = multisort(RECORDS, [SortKey(1)])
        assert [r[1] for r in out] == [
            90.0,
            90.0,
            100.0,
            120.0,
        ]

    def test_the_input_is_not_mutated(self):
        multisort(RECORDS, [SortKey(1)])
        assert RECORDS[0][2] == "Ada"


class TestRefusals:
    def test_no_keys_is_refused(self):
        with pytest.raises(Invalid):
            multisort(RECORDS, [])

    def test_a_column_out_of_range(self):
        with pytest.raises(Invalid):
            multisort(RECORDS, [SortKey(9)])

    def test_a_mixed_type_column_is_refused(self):
        bad = [["a", 1.0], ["b", "two"]]
        with pytest.raises(Invalid) as caught:
            multisort(bad, [SortKey(1)])
        assert "no order across types" in str(caught.value)
