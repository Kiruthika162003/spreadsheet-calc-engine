from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula


def run(formula: str):
    return evaluate(
        parse_formula(formula), lambda _r: None, full_table
    )


class TestDollar:
    def test_it_groups_and_signs(self):
        assert run("=DOLLAR(1234.5, 2)") == "$1,234.50"

    def test_the_minus_sits_outside_the_symbol(self):
        assert run("=DOLLAR(-1234.5, 2)") == "-$1,234.50"

    def test_it_rounds_to_the_penny(self):
        assert run("=DOLLAR(1234.567)") == "$1,234.57"

    def test_the_default_is_two_decimals(self):
        assert run("=DOLLAR(5)") == "$5.00"


class TestFixed:
    def test_grouping_without_a_symbol(self):
        assert run("=FIXED(1234.5, 1)") == "1,234.5"

    def test_the_no_commas_flag(self):
        assert run("=FIXED(1234.5, 1, TRUE)") == "1234.5"

    def test_a_negative_decimal_rounds_left(self):
        assert run("=FIXED(1234, -2)") == "1,200"

    def test_zero_decimals(self):
        assert run("=FIXED(1234.9, 0)") == "1,235"


class TestTheyReturnText:
    def test_a_whole_number_is_still_text(self):
        result = run("=FIXED(1000, 0)")
        assert isinstance(result, str)
        assert result == "1,000"

    def test_they_concatenate_into_a_sentence(self):
        assert (
            run('="Total: " & DOLLAR(2500, 0)')
            == "Total: $2,500"
        )
