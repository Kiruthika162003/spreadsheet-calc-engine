from __future__ import annotations

import pytest

from gridiron.ast import Binary, Bool, Call, Name, Number, Range, Ref, Unary
from gridiron.errors import Unparseable
from gridiron.parser import parse_formula


class TestPrecedence:
    def test_multiplication_beats_addition(self):
        tree = parse_formula("=1+2*3")
        assert isinstance(tree, Binary)
        assert tree.op == "+"
        assert isinstance(tree.right, Binary)
        assert tree.right.op == "*"

    def test_the_famous_case_lands_on_excels_side(self):
        tree = parse_formula("=-2^2")
        assert isinstance(tree, Binary)
        assert tree.op == "^"
        assert isinstance(tree.left, Unary)

    def test_the_caret_is_left_associative(self):
        tree = parse_formula("=2^3^2")
        assert isinstance(tree.left, Binary)
        assert tree.left.op == "^"

    def test_concat_sits_between_arithmetic_and_comparison(self):
        tree = parse_formula('=1+1&"x"=2')
        assert tree.op == "="
        assert tree.left.op == "&"
        assert tree.left.left.op == "+"

    def test_percent_is_postfix_division_and_stacks(self):
        tree = parse_formula("=50%%")
        assert tree.op == "/"
        assert tree.left.op == "/"
        assert tree.left.left == Number(value=50.0)

    def test_parentheses_override_everything(self):
        tree = parse_formula("=(1+2)*3")
        assert tree.op == "*"
        assert tree.left.op == "+"


class TestWords:
    def test_refs_ranges_names_and_booleans_classify(self):
        assert isinstance(parse_formula("=B7"), Ref)
        assert isinstance(parse_formula("=A1:C3"), Range)
        assert isinstance(parse_formula("=TAXRATE"), Name)
        assert parse_formula("=TRUE") == Bool(value=True)

    def test_function_calls_take_arguments(self):
        tree = parse_formula("=SUM(A1:A3, 5, B2)")
        assert isinstance(tree, Call)
        assert tree.function == "SUM"
        assert len(tree.args) == 3

    def test_the_empty_call_is_legal(self):
        assert parse_formula("=PI()") == Call(
            function="PI", args=()
        )

    def test_lowercase_references_normalize(self):
        assert parse_formula("=SUM(a1)").args[0] == parse_formula(
            "=SUM(A1)"
        ).args[0]


class TestRefsWalk:
    def test_every_reference_is_discoverable(self):
        tree = parse_formula("=A1 + SUM(B1:B3) * C9")
        found = list(tree.refs())
        assert len(found) == 3


class TestRefusals:
    def test_the_error_names_the_position_in_the_body(self):
        with pytest.raises(Unparseable) as caught:
            parse_formula("=1+)")
        assert "position 2" in str(caught.value)

    def test_a_complete_formula_rejects_leftovers(self):
        with pytest.raises(Unparseable) as caught:
            parse_formula("=1 2")
        assert "already complete" in str(caught.value)

    def test_the_dangling_operator_is_named(self):
        with pytest.raises(Unparseable) as caught:
            parse_formula("=1+")
        assert "ends where more was expected" in str(caught.value)
