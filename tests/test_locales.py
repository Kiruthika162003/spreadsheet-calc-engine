from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.locales import (
    COMMA,
    POINT,
    parse_number,
    render_number,
    translate_formula,
)


class TestRendering:
    def test_both_halves_of_the_world(self):
        assert render_number(1234.56, POINT) == "1,234.56"
        assert render_number(1234.56, COMMA) == "1.234,56"

    def test_grouping_counts_in_threes(self):
        assert (
            render_number(1234567.0, POINT, 0)
            == "1,234,567"
        )

    def test_negatives_keep_their_sign_outside(self):
        assert render_number(-9876.5, COMMA) == "-9.876,50"

    def test_zero_decimals_drop_the_mark(self):
        assert render_number(42.0, COMMA, 0) == "42"


class TestParsing:
    def test_each_locale_reads_its_own_notation(self):
        assert parse_number("1,234.56", POINT) == 1234.56
        assert parse_number("1.234,56", COMMA) == 1234.56

    def test_misplaced_separators_are_refused(self):
        with pytest.raises(Invalid) as caught:
            parse_number("1,23,456", POINT)
        assert "threes" in str(caught.value)

    def test_a_leading_group_may_be_short_not_long(self):
        assert parse_number("12,345", POINT) == 12345.0
        with pytest.raises(Invalid):
            parse_number("1234,567", POINT)

    def test_two_decimal_marks_are_named(self):
        with pytest.raises(Invalid) as caught:
            parse_number("1.2.3", POINT)
        assert "two decimal marks" in str(caught.value)

    def test_signs_are_honored(self):
        assert parse_number("-1.234,50", COMMA) == -1234.5


class TestTranslation:
    def test_the_costume_change(self):
        point_form = '=IF(A1>1.5, "yes, indeed", SUM(B1, 2.25))'
        comma_form = translate_formula(
            point_form, POINT, COMMA
        )
        assert comma_form == (
            '=IF(A1>1,5; "yes, indeed"; SUM(B1; 2,25))'
        )

    def test_the_round_trip_is_the_identity(self):
        point_form = '=IF(A1>1.5, "a;b, c", MAX(1.25, 2))'
        there = translate_formula(point_form, POINT, COMMA)
        back = translate_formula(there, COMMA, POINT)
        assert back == point_form

    def test_strings_keep_their_commas(self):
        translated = translate_formula(
            '="Hello, world"', POINT, COMMA
        )
        assert translated == '="Hello, world"'

    def test_escaped_quotes_do_not_end_the_string(self):
        translated = translate_formula(
            '="say ""hi, there"", ok"&A1', POINT, COMMA
        )
        assert '""hi, there""' in translated

    def test_table_names_keep_their_dots(self):
        translated = translate_formula(
            "=SUM(ORDERS.AMOUNT, 1.5)", POINT, COMMA
        )
        assert translated == "=SUM(ORDERS.AMOUNT; 1,5)"

    def test_an_unclosed_string_is_refused(self):
        with pytest.raises(Invalid) as caught:
            translate_formula('="oops', POINT, COMMA)
        assert "inside a string literal" in str(caught.value)

    def test_translating_to_yourself_is_free(self):
        formula = "=SUM(A1, 1.5)"
        assert (
            translate_formula(formula, POINT, POINT)
            == formula
        )
