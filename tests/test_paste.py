from __future__ import annotations

from gridiron.paste import shifted_formula


class TestTheDollarContract:
    def test_relative_parts_move_and_absolute_parts_pin(self):
        assert shifted_formula("=A1+$A$1", 2, 3) == (
            "=(D3+$A$1)"
        )

    def test_the_mixed_flavors_pin_one_axis_each(self):
        assert shifted_formula("=$A1+A$1", 5, 5) == (
            "=($A6+F$1)"
        )

    def test_ranges_shift_as_rectangles(self):
        assert shifted_formula("=SUM(A1:B2)", 1, 1) == (
            "=SUM(B2:C3)"
        )


class TestTreeNotText:
    def test_text_that_looks_like_a_ref_survives(self):
        assert shifted_formula('="B12"&A1', 1, 0) == (
            '=("B12"&A2)'
        )

    def test_function_names_are_not_renumbered(self):
        moved = shifted_formula("=SUM(A1)", 0, 1)
        assert moved.startswith("=SUM(")

    def test_quotes_inside_strings_re_escape(self):
        assert shifted_formula('="say ""hi"""', 3, 3) == (
            '="say ""hi"""'
        )


class TestTheEdgeApology:
    def test_the_off_sheet_reference_lands_as_ref_error(self):
        assert shifted_formula("=A1+5", -1, 0) == "=(#REF!+5)"

    def test_the_absolute_reference_survives_the_same_shift(self):
        assert shifted_formula("=$A$1+5", -1, 0) == (
            "=($A$1+5)"
        )


class TestNormalization:
    def test_the_rewritten_formula_is_normalized_and_says_so(self):
        assert shifted_formula("=a1  +  2", 0, 0) == "=(A1+2)"
