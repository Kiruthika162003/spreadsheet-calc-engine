from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.numberwords import (
    spell_integer,
    spell_money,
    spell_number,
)


class TestIntegers:
    def test_the_small_cases(self):
        assert spell_integer(0) == "zero"
        assert spell_integer(7) == "seven"
        assert spell_integer(19) == "nineteen"

    def test_the_tens_hyphenate(self):
        assert spell_integer(42) == "forty-two"
        assert spell_integer(80) == "eighty"

    def test_hundreds_carry_no_and(self):
        assert spell_integer(105) == "one hundred five"
        assert spell_integer(999) == (
            "nine hundred ninety-nine"
        )

    def test_the_scale_words(self):
        assert spell_integer(1000) == "one thousand"
        assert spell_integer(1234567) == (
            "one million two hundred thirty-four "
            "thousand five hundred sixty-seven"
        )

    def test_a_negative_is_not_a_check(self):
        with pytest.raises(Invalid) as caught:
            spell_integer(-5)
        assert "not a check that exists" in str(caught.value)

    def test_an_unnameable_amount_refuses(self):
        with pytest.raises(Invalid) as caught:
            spell_integer(10**15)
        assert "switch to digits" in str(caught.value)


class TestMoney:
    def test_the_cents_are_a_fraction_not_words(self):
        assert spell_money(105.50) == (
            "one hundred five dollars and 50/100"
        )

    def test_the_and_separates_dollars_from_cents(self):
        # Exactly one "and", between dollars and cents.
        assert spell_money(125.05).count(" and ") == 1

    def test_one_dollar_is_singular(self):
        assert spell_money(1.00) == "one dollar and 00/100"

    def test_zero_dollars_still_spells(self):
        assert spell_money(0.25) == "zero dollars and 25/100"

    def test_rounding_is_to_the_even_cent(self):
        assert spell_money(1.005) == (
            "one dollar and 00/100"
        )
        assert spell_money(2.675) == (
            "two dollars and 68/100"
        )

    def test_a_negative_check_is_refused(self):
        with pytest.raises(Invalid) as caught:
            spell_money(-5.0)
        assert "not a document that exists" in str(
            caught.value
        )


class TestSpellNumber:
    def test_whole_numbers_only(self):
        assert spell_number(2026.0) == (
            "two thousand twenty-six"
        )

    def test_a_fraction_is_refused(self):
        with pytest.raises(Invalid) as caught:
            spell_number(2.5)
        assert "use spell_money" in str(caught.value)
