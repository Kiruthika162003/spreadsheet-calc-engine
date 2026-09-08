from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

WORLD = {(0, 0): "a", (0, 1): 1.0, (1, 0): "b", (1, 1): 2.0}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(parse_formula(formula), lookup, full_table)


class TestIfs:
    def test_the_first_true_condition_wins(self):
        assert run("=IFS(1>2, 10, 3>2, 20, 5>2, 30)") == 20.0

    def test_no_true_condition_is_na(self):
        outcome = run("=IFS(1>2, 10, 2>3, 20)")
        assert outcome.code == "#N/A"
        assert "left unfinished" in outcome.note

    def test_a_later_error_is_never_reached(self):
        assert run("=IFS(1>0, 42, 1>0, 1/0)") == 42.0


class TestSwitch:
    def test_a_matching_candidate(self):
        assert (
            run('=SWITCH(2, 1, "one", 2, "two", "other")')
            == "two"
        )

    def test_the_default_when_nothing_matches(self):
        assert (
            run('=SWITCH(9, 1, "one", "default")')
            == "default"
        )

    def test_no_match_and_no_default_is_na(self):
        outcome = run('=SWITCH(9, 1, "one")')
        assert outcome.code == "#N/A"

    def test_the_unchosen_arm_is_not_evaluated(self):
        assert run('=SWITCH(1, 1, 7, 2, 1/0)') == 7.0


class TestChoose:
    def test_it_indexes_one_based(self):
        assert run("=CHOOSE(2, 100, 200, 300)") == 200.0

    def test_an_index_outside_is_refused(self):
        outcome = run("=CHOOSE(5, 100, 200)")
        assert outcome.code == "#VALUE!"
        assert "did not mean" in outcome.note

    def test_only_the_chosen_entry_evaluates(self):
        assert run("=CHOOSE(1, 9, 1/0)") == 9.0


class TestIfna:
    def test_it_catches_only_na(self):
        assert (
            run('=IFNA(VLOOKUP("z", A1:B2, 2), 99)') == 99.0
        )

    def test_it_lets_other_errors_through(self):
        outcome = run("=IFNA(1/0, 99)")
        assert outcome.code == "#DIV/0!"

    def test_a_clean_value_passes_untouched(self):
        assert run("=IFNA(5, 99)") == 5.0
