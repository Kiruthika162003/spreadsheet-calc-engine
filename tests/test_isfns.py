from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.values import ErrorValue

WORLD = {
    (0, 0): 42.0,
    (1, 0): "label",
    (2, 0): "",
    (3, 0): True,
    (4, 0): ErrorValue(code="#DIV/0!"),
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestTheOneRule:
    def test_no_is_function_ever_returns_an_error(self):
        assert run("=ISERROR(A5)") is True
        assert run("=ISERROR(1/0)") is True
        assert run("=ISNUMBER(A5)") is False
        assert run("=ISTEXT(A5)") is False

    def test_the_inspector_does_not_faint(self):
        assert run("=IF(ISERROR(1/0), 99, 1)") == 99.0


class TestBlankness:
    def test_truly_absent_versus_emptied(self):
        assert run("=ISBLANK(Z9)") is True
        assert run("=ISBLANK(A3)") is False
        assert run("=ISTEXT(A3)") is True

    def test_isblank_of_an_expression_asks_the_value(self):
        assert run("=ISBLANK(A1)") is False


class TestKinds:
    def test_isnumber_refuses_to_be_talked_into_booleans(self):
        assert run("=ISNUMBER(A1)") is True
        assert run("=ISNUMBER(A4)") is False
        assert run("=ISLOGICAL(A4)") is True

    def test_text_is_text_even_when_numeric_looking(self):
        assert run('=ISTEXT("42")') is True
        assert run('=ISNUMBER("42")') is False
