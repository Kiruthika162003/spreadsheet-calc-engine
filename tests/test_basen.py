from __future__ import annotations

import pytest

from gridiron.basen import from_base, to_base
from gridiron.errors import Invalid


class TestToBase:
    def test_common_bases(self):
        assert to_base(255, 16) == "FF"
        assert to_base(255, 2) == "11111111"
        assert to_base(1295, 36) == "ZZ"

    def test_zero(self):
        assert to_base(0, 16) == "0"

    def test_min_width_pads(self):
        assert to_base(5, 2, min_width=8) == "00000101"

    def test_min_width_never_truncates(self):
        assert to_base(255, 16, min_width=1) == "FF"

    def test_a_base_out_of_range_is_refused(self):
        with pytest.raises(Invalid) as caught:
            to_base(10, 37)
        assert "run out of letters" in str(caught.value)

    def test_a_negative_is_refused(self):
        with pytest.raises(Invalid) as caught:
            to_base(-1, 16)
        assert "no sign convention" in str(caught.value)


class TestFromBase:
    def test_reading_back(self):
        assert from_base("FF", 16) == 255
        assert from_base("ZZ", 36) == 1295

    def test_case_and_space_tolerant(self):
        assert from_base("  ff  ", 16) == 255

    def test_a_foreign_digit_is_refused(self):
        with pytest.raises(Invalid) as caught:
            from_base("Z", 16)
        assert "looks right" in str(caught.value)


class TestRoundTrip:
    def test_every_base_is_a_bijection(self):
        failures = [
            (n, b)
            for b in range(2, 37)
            for n in range(0, 200)
            if from_base(to_base(n, b), b) != n
        ]
        assert failures == []
