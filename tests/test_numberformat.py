from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.numberformat import NumberFormat
from gridiron.values import ErrorValue


def fmt(code: str) -> NumberFormat:
    return NumberFormat.parse(code)


class TestTheOneRule:
    def test_the_value_never_changes_only_its_clothes(self):
        assert fmt("0.00").apply(2.71828) == "2.72"
        assert fmt("0").apply(2.71828) == "3"

    def test_non_numbers_pass_through_unstyled(self):
        assert fmt("0.00").apply("label") == "label"
        assert fmt("0.00").apply(None) == ""
        assert fmt("0.00").apply(
            ErrorValue(code="#REF!")
        ) == "#REF!"


class TestTheCodeLanguage:
    def test_the_comma_groups_thousands(self):
        assert fmt("#,##0").apply(1234567.0) == "1,234,567"
        assert fmt("#,##0.00").apply(1234.5) == "1,234.50"

    def test_the_percent_multiplies_the_display_only(self):
        assert fmt("0.0%").apply(0.1234) == "12.3%"

    def test_the_negative_section_takes_over(self):
        code = fmt("#,##0.00;(#,##0.00)")
        assert code.apply(1234.5) == "1,234.50"
        assert code.apply(-1234.5) == "(1,234.50)"

    def test_without_a_negative_section_the_minus_stays(self):
        assert fmt("0.00").apply(-2.5) == "-2.50"


class TestRefusals:
    def test_unknown_characters_refuse_to_guess_about_money(self):
        with pytest.raises(Invalid) as caught:
            NumberFormat.parse("0.00E+00")
        assert "refused" in str(caught.value)

    def test_three_sections_are_too_many(self):
        with pytest.raises(Invalid):
            NumberFormat.parse("0;0;0")

    def test_the_empty_code_dresses_nothing(self):
        with pytest.raises(Invalid):
            NumberFormat.parse("")
