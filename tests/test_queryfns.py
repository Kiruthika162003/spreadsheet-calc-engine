from __future__ import annotations

import pytest

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

DATABASE = (
    ("Name", "Dept", "Salary"),
    ("Ada", "Eng", 120.0),
    ("Grace", "Eng", 130.0),
    ("Alan", "Ops", 90.0),
    ("Edsger", "Eng", 110.0),
    ("Barbara", "Ops", 95.0),
)

CRITERIA = {
    (0, 4): "Dept",
    (1, 4): "Eng",
    (0, 5): "Salary",
    (1, 5): ">115",
}


def world():
    cells = {}
    for row_index, row in enumerate(DATABASE):
        for col_index, value in enumerate(row):
            cells[(row_index, col_index)] = value
    cells.update(CRITERIA)
    return cells


WORLD = world()


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestTheAndRow:
    def test_conditions_in_one_row_and_together(self):
        assert (
            run('=DSUM(A1:C6, "Salary", E1:F2)') == 250.0
        )

    def test_the_field_can_be_a_number(self):
        assert run("=DSUM(A1:C6, 3, E1:F2)") == 250.0

    def test_daverage_and_the_bounds(self):
        assert (
            run('=DAVERAGE(A1:C6, "Salary", E1:F2)') == 125.0
        )
        assert run('=DMIN(A1:C6, "Salary", E1:F2)') == 120.0
        assert run('=DMAX(A1:C6, "Salary", E1:F2)') == 130.0

    def test_dcount_counts_numeric_matches(self):
        assert run('=DCOUNT(A1:C6, "Salary", E1:F2)') == 2.0


class TestTheOrRows:
    def test_separate_rows_or_together(self):
        or_world = dict(WORLD)
        or_world[(0, 4)] = "Dept"
        or_world[(1, 4)] = "Eng"
        or_world[(2, 4)] = "Ops"
        del or_world[(0, 5)]
        del or_world[(1, 5)]

        def or_lookup(ref: CellRef):
            return or_world.get(ref.key())

        outcome = evaluate(
            parse_formula('=DSUM(A1:C6, "Salary", E1:E3)'),
            or_lookup,
            full_table,
        )
        assert outcome == 545.0

    def test_a_blank_criteria_cell_constrains_nothing(self):
        assert (
            run('=DSUM(A1:C6, "Salary", E1:E2)') == 360.0
        )


class TestDget:
    def test_exactly_one_match_returns_the_value(self):
        one_world = dict(WORLD)
        one_world[(1, 5)] = ">125"

        def one_lookup(ref: CellRef):
            return one_world.get(ref.key())

        outcome = evaluate(
            parse_formula('=DGET(A1:C6, "Name", F1:F2)'),
            one_lookup,
            full_table,
        )
        assert outcome == "Grace"

    def test_two_matches_at_the_first_probe_refuse(self):
        outcome = run('=DGET(A1:C6, "Name", F1:F2)')
        assert outcome.code == "#NUM!"
        assert "2 records match" in outcome.note

    def test_several_matches_are_a_coin_flip(self):
        outcome = run('=DGET(A1:C6, "Name", E1:E2)')
        assert outcome.code == "#NUM!"
        assert "3 records match" in outcome.note

    def test_no_match_has_nothing_to_get(self):
        no_world = dict(WORLD)
        no_world[(1, 5)] = ">999"

        def no_lookup(ref: CellRef):
            return no_world.get(ref.key())

        outcome = evaluate(
            parse_formula('=DGET(A1:C6, "Name", F1:F2)'),
            no_lookup,
            full_table,
        )
        assert outcome.code == "#VALUE!"
        assert "nothing to get" in outcome.note


class TestRefusals:
    def test_an_orphan_criteria_header_is_named(self):
        orphan_world = dict(WORLD)
        orphan_world[(0, 5)] = "Bonus"

        def orphan_lookup(ref: CellRef):
            return orphan_world.get(ref.key())

        outcome = evaluate(
            parse_formula('=DSUM(A1:C6, "Salary", E1:F2)'),
            orphan_lookup,
            full_table,
        )
        assert outcome.code == "#VALUE!"
        assert "orphan" in outcome.note

    def test_an_unknown_field_lists_the_header_row(self):
        outcome = run('=DSUM(A1:C6, "Bonus", E1:F2)')
        assert outcome.code == "#VALUE!"
        assert "NAME, DEPT, SALARY" in outcome.note

    def test_a_field_number_off_the_edge(self):
        outcome = run("=DSUM(A1:C6, 4, E1:F2)")
        assert outcome.code == "#VALUE!"
        assert "3 column(s)" in outcome.note

    def test_an_empty_criteria_region_is_refused(self):
        empty_world = dict(WORLD)
        del empty_world[(1, 4)]
        del empty_world[(0, 5)]
        del empty_world[(1, 5)]

        def empty_lookup(ref: CellRef):
            return empty_world.get(ref.key())

        outcome = evaluate(
            parse_formula('=DSUM(A1:C6, "Salary", E1:E2)'),
            empty_lookup,
            full_table,
        )
        assert outcome.code == "#VALUE!"
        assert "plain aggregate" in outcome.note

    def test_daverage_over_no_matches_divides_by_zero(self):
        none_world = dict(WORLD)
        none_world[(1, 5)] = ">999"

        def none_lookup(ref: CellRef):
            return none_world.get(ref.key())

        outcome = evaluate(
            parse_formula(
                '=DAVERAGE(A1:C6, "Salary", F1:F2)'
            ),
            none_lookup,
            full_table,
        )
        assert outcome.code == "#DIV/0!"

    def test_the_shared_micro_grammar_speaks_wildcards(self):
        wild_world = dict(WORLD)
        wild_world[(0, 5)] = "Name"
        wild_world[(1, 5)] = "A*"
        del wild_world[(0, 4)]
        del wild_world[(1, 4)]

        def wild_lookup(ref: CellRef):
            return wild_world.get(ref.key())

        outcome = evaluate(
            parse_formula('=DSUM(A1:C6, "Salary", F1:F2)'),
            wild_lookup,
            full_table,
        )
        assert outcome == pytest.approx(210.0)
