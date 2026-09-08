from __future__ import annotations

import pytest

from gridiron.checkdigit import (
    isbn10_valid,
    isbn13_valid,
    luhn_check_digit,
    luhn_valid,
)
from gridiron.errors import Invalid


class TestLuhn:
    def test_a_valid_card_number(self):
        assert luhn_valid("4539578763621486") is True

    def test_a_single_digit_typo_is_caught(self):
        assert luhn_valid("4539578763621487") is False

    def test_hyphens_and_spaces_are_ignored(self):
        assert luhn_valid("4539 5787 6362 1486") is True

    def test_the_completing_check_digit(self):
        assert luhn_check_digit("453957876362148") == 6

    def test_non_digits_are_refused(self):
        with pytest.raises(Invalid) as caught:
            luhn_valid("4539abcd")
        assert "malformed input" in str(caught.value)


class TestIsbn10:
    def test_a_valid_isbn10(self):
        assert isbn10_valid("0306406152") is True

    def test_the_x_check_digit(self):
        assert isbn10_valid("080442957X") is True

    def test_a_wrong_length_fails(self):
        assert isbn10_valid("12345") is False

    def test_an_x_in_the_wrong_place_is_refused(self):
        with pytest.raises(Invalid) as caught:
            isbn10_valid("X306406152")
        assert "final ISBN-10 position" in str(caught.value)


class TestIsbn13:
    def test_a_valid_isbn13(self):
        assert isbn13_valid("9780306406157") is True

    def test_a_typo_is_caught(self):
        assert isbn13_valid("9780306406158") is False

    def test_a_wrong_length_fails(self):
        assert isbn13_valid("978030640615") is False
