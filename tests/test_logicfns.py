from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.values import ErrorValue

WORLD = {
    (0, 0): 10.0,
    (1, 0): 0.0,
    (0, 1): ErrorValue(code="#REF!"),
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestAndOrXorNot:
    def test_the_gates_answer_over_mixed_arguments(self):
        assert run("=AND(A1>5, A2=0)") is True
        assert run("=OR(A1<5, A2=0)") is True
        assert run("=AND(A1>5, A2>5)") is False
        assert run("=NOT(A2)") is True

    def test_numbers_are_truthy_by_nonzero(self):
        assert run("=AND(A1, 1)") is True
        assert run("=OR(A2, 0)") is False

    def test_xor_counts_odd_truths(self):
        assert run("=XOR(TRUE, TRUE, TRUE)") is True
        assert run("=XOR(TRUE, TRUE)") is False

    def test_text_is_not_a_truth_value(self):
        assert run('=AND(TRUE, "yes")').code == "#VALUE!"

    def test_the_empty_and_is_an_incident_not_a_truth(self):
        outcome = run("=AND()")
        assert outcome.code == "#VALUE!"
        assert "spreadsheet's incident" in outcome.note


class TestEagerness:
    def test_and_is_not_lazy_so_errors_always_surface(self):
        assert run("=AND(A2=0, B1)").code == "#REF!"
        assert run("=OR(A1>5, B1)").code == "#REF!"


class TestIferror:
    def test_the_catch_returns_the_fallback_only_on_error(self):
        assert run("=IFERROR(A1/A2, 0-1)") == -1.0
        assert run("=IFERROR(A1/2, 0-1)") == 5.0

    def test_the_fallback_may_itself_err(self):
        outcome = run("=IFERROR(1/0, B1)")
        assert outcome.code == "#REF!"


class TestMod:
    def test_mod_follows_the_divisor_sign(self):
        assert run("=MOD(7, 3)") == 1.0
        assert run("=MOD(0-7, 3)") == 2.0
        assert run("=MOD(7, 0-3)") == -2.0

    def test_mod_by_zero_is_the_family_error(self):
        assert run("=MOD(7, 0)").code == "#DIV/0!"
