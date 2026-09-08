from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.volatilefns import VolatileContext

WORLD = {
    (0, 0): 5.0,
    (1, 0): 10.0,
    (2, 0): 20.0,
    (3, 0): 30.0,
}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestBinding:
    def test_a_single_name_is_visible_to_the_body(self):
        assert run("=LET(x, A1*2, x+1)") == 11.0

    def test_a_later_name_builds_on_an_earlier_one(self):
        assert run("=LET(x, A1*2, y, x+1, y*y)") == 121.0

    def test_a_name_shadows_nothing_it_should_not(self):
        assert run("=LET(total, SUM(A1:A4), total/4)") == (
            16.25
        )

    def test_names_reach_into_nested_calls(self):
        assert (
            run("=LET(base, 10, IF(A1>base, base, A1))")
            == 5.0
        )


class TestRefusals:
    def test_an_even_argument_count_is_refused(self):
        outcome = run("=LET(x, 5)")
        assert outcome.code == "#VALUE!"
        assert "odd count of at least three" in outcome.note

    def test_a_cell_reference_as_a_name_is_refused(self):
        outcome = run("=LET(A1, 5, A1+1)")
        assert outcome.code == "#VALUE!"
        assert "wearing a variable's clothes" in outcome.note


class TestErrorsAndVolatiles:
    def test_an_unused_error_does_not_surface(self):
        assert run("=LET(x, 1/0, 42)") == 42.0

    def test_a_used_error_carries_through(self):
        outcome = run("=LET(x, 1/0, x+1)")
        assert outcome.code == "#DIV/0!"

    def test_a_bound_value_is_evaluated_only_once(self):
        context = VolatileContext(seed=1, today_serial=100)
        volatile = context.make_functions()

        def table(name: str):
            found = volatile.get(name)
            return found if found is not None else full_table(name)

        formula = parse_formula("=LET(r, RAND(), r-r)")
        outcome = evaluate(formula, lookup, table)
        # If RAND fired twice, r-r would be a nonzero
        # difference of two draws; once-evaluation makes it 0.
        assert outcome == 0.0
