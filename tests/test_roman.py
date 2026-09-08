from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.roman import from_roman, to_roman


class TestToRoman:
    def test_the_subtractive_pairs(self):
        assert to_roman(4) == "IV"
        assert to_roman(9) == "IX"
        assert to_roman(40) == "XL"
        assert to_roman(90) == "XC"

    def test_a_famous_year(self):
        assert to_roman(1994) == "MCMXCIV"

    def test_the_top_of_the_range(self):
        assert to_roman(3999) == "MMMCMXCIX"

    def test_out_of_range_is_refused(self):
        for bad in (0, -1, 4000):
            with pytest.raises(Invalid):
                to_roman(bad)


class TestFromRoman:
    def test_it_parses_the_canonical_form(self):
        assert from_roman("MCMXCIV") == 1994
        assert from_roman("IV") == 4

    def test_case_and_whitespace_are_tolerated(self):
        assert from_roman("  xiv  ") == 14

    def test_additive_overruns_are_refused(self):
        with pytest.raises(Invalid):
            from_roman("IIII")

    def test_bad_subtractions_are_refused(self):
        with pytest.raises(Invalid):
            from_roman("IC")

    def test_gibberish_is_refused(self):
        with pytest.raises(Invalid):
            from_roman("ABC")


class TestRoundTrip:
    def test_every_number_survives(self):
        for n in (1, 4, 49, 88, 500, 1000, 2024, 3999):
            assert from_roman(to_roman(n)) == n

    def test_the_whole_range_is_a_bijection(self):
        failures = [
            n
            for n in range(1, 4000)
            if from_roman(to_roman(n)) != n
        ]
        assert failures == []
