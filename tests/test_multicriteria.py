from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

WORLD = {
    (0, 0): "East",
    (1, 0): "West",
    (2, 0): "East",
    (3, 0): "East",
    (0, 1): "Q1",
    (1, 1): "Q1",
    (2, 1): "Q2",
    (3, 1): "Q1",
    (0, 2): 100.0,
    (1, 2): 200.0,
    (2, 2): 150.0,
    (3, 2): 300.0,
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestAndAcrossCriteria:
    def test_sumifs_joins_conditions(self):
        assert run(
            '=SUMIFS(C1:C4, A1:A4, "East", B1:B4, "Q1")'
        ) == 400.0

    def test_countifs_is_all_pairs(self):
        assert run('=COUNTIFS(A1:A4, "East")') == 3.0
        assert (
            run('=COUNTIFS(A1:A4, "East", B1:B4, "Q1")')
            == 2.0
        )

    def test_averageifs_over_the_matches(self):
        assert run(
            '=AVERAGEIFS(C1:C4, A1:A4, "East", B1:B4, "Q1")'
        ) == 200.0

    def test_maxifs_and_minifs(self):
        assert run('=MAXIFS(C1:C4, A1:A4, "East")') == 300.0
        assert run('=MINIFS(C1:C4, A1:A4, "East")') == 100.0


class TestCriteriaGrammar:
    def test_a_comparison_criterion(self):
        assert run('=SUMIFS(C1:C4, C1:C4, ">150")') == 500.0

    def test_a_wildcard_criterion(self):
        assert run('=COUNTIFS(A1:A4, "E*")') == 3.0


class TestRefusalsAndEdges:
    def test_a_mismatched_range_is_refused(self):
        outcome = run('=SUMIFS(C1:C4, A1:A3, "East")')
        assert outcome.code == "#VALUE!"
        assert "the wrong rows" in outcome.note

    def test_averageifs_over_nothing_is_undefined(self):
        outcome = run('=AVERAGEIFS(C1:C4, A1:A4, "South")')
        assert outcome.code == "#DIV/0!"
        assert "not zero" in outcome.note

    def test_a_bad_argument_count_is_refused(self):
        outcome = run('=SUMIFS(C1:C4, A1:A4)')
        assert outcome.code == "#VALUE!"

    def test_maxifs_over_nothing_is_zero(self):
        # The incumbent returns 0 for MAXIFS with no match.
        assert run('=MAXIFS(C1:C4, A1:A4, "South")') == 0.0
