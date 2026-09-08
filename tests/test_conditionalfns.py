from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

LEDGER = {
    (0, 0): "apples", (0, 1): 40.0,
    (1, 0): "bread", (1, 1): 15.0,
    (2, 0): "apricots", (2, 1): 22.0,
    (3, 0): "cheese", (3, 1): 8.0,
    (4, 0): "apples", (4, 1): 10.0,
}


def lookup(ref: CellRef):
    return LEDGER.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestCountif:
    def test_text_and_wildcard_criteria_count(self):
        assert run('=COUNTIF(A1:A5, "apples")') == 2.0
        assert run('=COUNTIF(A1:A5, "ap*")') == 3.0

    def test_numeric_comparisons_count(self):
        assert run('=COUNTIF(B1:B5, ">10")') == 3.0

    def test_empty_cells_never_match(self):
        assert run('=COUNTIF(A1:A9, "<>zzz")') == 5.0


class TestSumif:
    def test_the_offset_fold_region_pays(self):
        assert run('=SUMIF(A1:A5, "apples", B1:B5)') == 50.0
        assert run('=SUMIF(A1:A5, "ap*", B1:B5)') == 72.0

    def test_the_two_region_form_folds_itself(self):
        assert run('=SUMIF(B1:B5, ">10")') == 77.0

    def test_mismatched_shapes_move_money_between_quarters(self):
        outcome = run('=SUMIF(A1:A5, "apples", B1:B3)')
        assert outcome.code == "#VALUE!"
        assert "moves money between quarters" in outcome.note


class TestAverageif:
    def test_the_average_of_survivors(self):
        assert run('=AVERAGEIF(A1:A5, "apples", B1:B5)') == 25.0

    def test_zero_survivors_quote_the_criterion(self):
        outcome = run('=AVERAGEIF(A1:A5, "mangoes", B1:B5)')
        assert outcome.code == "#DIV/0!"
        assert "'mangoes'" in outcome.note

    def test_numeric_criteria_arrive_as_numbers_too(self):
        assert run("=COUNTIF(B1:B5, 40)") == 1.0
