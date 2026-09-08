from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.values import (
    ErrorValue,
    add,
    divide,
    first_error,
    is_error,
    multiply,
    render,
    subtract,
    to_number,
)


class TestErrorValues:
    def test_only_known_codes_exist(self):
        with pytest.raises(Invalid) as caught:
            ErrorValue(code="#OOPS!")
        assert "one bug becomes two" in str(caught.value)

    def test_any_operation_touching_an_error_yields_it(self):
        poison = ErrorValue(code="#REF!")
        assert add(poison, 5.0) is poison
        assert multiply(3.0, poison) is poison
        assert divide(poison, 0.0) is poison

    def test_the_first_error_wins_on_ties(self):
        first = ErrorValue(code="#REF!")
        second = ErrorValue(code="#DIV/0!")
        assert first_error(first, second) is first


class TestCoercion:
    def test_booleans_count_and_text_does_not(self):
        assert add(True, True) == 2.0
        laundered = add("12", 1.0)
        assert is_error(laundered)
        assert laundered.code == "#VALUE!"

    def test_empty_is_zero_in_arithmetic(self):
        assert add(None, 7.0) == 7.0
        assert to_number(None) == 0.0


class TestArithmetic:
    def test_the_zero_divisor_keeps_the_grid_working(self):
        outcome = divide(10.0, 0.0)
        assert is_error(outcome)
        assert outcome.code == "#DIV/0!"
        assert "the grid keeps working" in outcome.note

    def test_subtract_rides_on_add_and_multiply(self):
        assert subtract(10.0, 4.0) == 6.0
        assert subtract(10.0, ErrorValue(code="#NUM!")).code == (
            "#NUM!"
        )

    def test_ordinary_division_is_ordinary(self):
        assert divide(9.0, 2.0) == 4.5


class TestRendering:
    def test_whole_floats_print_like_integers(self):
        assert render(42.0) == "42"
        assert render(2.5) == "2.5"

    def test_the_rest_of_the_menagerie(self):
        assert render(None) == ""
        assert render(True) == "TRUE"
        assert render("label") == "label"
        assert render(ErrorValue(code="#CYCLE!")) == "#CYCLE!"
