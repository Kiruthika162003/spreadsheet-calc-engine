from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.sheet import Sheet
from gridiron.volatilefns import (
    VolatileContext,
    is_volatile,
    missing_context_functions,
    volatile_census,
)


def lookup(_ref: CellRef):
    return None


def table_with(context_functions):
    def resolve(name: str):
        found = context_functions.get(name)
        if found is not None:
            return found
        return full_table(name)

    return resolve


def run(formula: str, context: VolatileContext):
    return evaluate(
        parse_formula(formula),
        lookup,
        table_with(context.make_functions()),
    )


class TestDeterminism:
    def test_the_same_seed_rolls_the_same_dice(self):
        first = VolatileContext(seed=42, today_serial=9000)
        second = VolatileContext(seed=42, today_serial=9000)
        rolls_a = [run("=RAND()", first) for _ in range(5)]
        rolls_b = [run("=RAND()", second) for _ in range(5)]
        assert rolls_a == rolls_b
        assert len(set(rolls_a)) == 5

    def test_rand_lands_in_the_unit_interval(self):
        context = VolatileContext(seed=7, today_serial=9000)
        for _ in range(100):
            roll = run("=RAND()", context)
            assert 0.0 < roll < 1.0

    def test_today_is_the_injected_serial(self):
        context = VolatileContext(seed=1, today_serial=8888)
        assert run("=TODAY()", context) == 8888.0
        assert run("=TODAY()+7", context) == 8895.0


class TestTheRefusal:
    def test_no_context_means_name_error_with_the_policy(self):
        refusers = missing_context_functions()
        outcome = evaluate(
            parse_formula("=RAND()"),
            lookup,
            table_with(refusers),
        )
        assert outcome.code == "#NAME?"
        assert "no ambient clock" in outcome.note

    def test_arguments_are_refused(self):
        context = VolatileContext(seed=1, today_serial=1)
        assert run("=RAND(1)", context).code == "#VALUE!"

    def test_the_calendar_bound_holds(self):
        with pytest.raises(Invalid):
            VolatileContext(seed=1, today_serial=0)


class TestTheTaint:
    def test_volatility_is_contagious_through_the_tree(self):
        assert is_volatile(parse_formula("=RAND()*10"))
        assert is_volatile(parse_formula("=SUM(A1, TODAY())"))
        assert not is_volatile(parse_formula("=A1+B2"))

    def test_the_census_names_the_tainted_cells(self):
        sheet = Sheet()
        sheet.set_formula(CellRef.parse("B1"), "=RAND()")
        sheet.set_formula(CellRef.parse("B2"), "=A1*2")
        census = volatile_census(sheet.formula_cells())
        assert census.startswith("1 volatile cell(s) (B1)")
        assert "cannot claim the rest is current" in census

    def test_the_clean_sheet_is_current_until_the_next_edit(self):
        sheet = Sheet()
        sheet.set_formula(CellRef.parse("B1"), "=A1*2")
        assert volatile_census(
            sheet.formula_cells()
        ).startswith("no volatile cells")
