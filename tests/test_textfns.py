from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import catalog, full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

WORLD = {(0, 0): "  Quarterly   Ledger  ", (1, 0): 42.0}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestOneBased:
    def test_mid_is_one_based_like_its_users(self):
        assert run('=MID("ledger", 1, 3)') == "led"
        assert run('=MID("ledger", 4, 3)') == "ger"

    def test_the_zero_start_names_the_convention(self):
        outcome = run('=MID("ledger", 0, 3)')
        assert outcome.code == "#VALUE!"
        assert "one-based" in outcome.note


class TestEdges:
    def test_left_past_the_end_returns_everything(self):
        assert run('=LEFT("abc", 99)') == "abc"

    def test_the_negative_count_is_not_clamped(self):
        outcome = run('=LEFT("abc", 1-5)')
        assert outcome.code == "#VALUE!"
        assert "hide the arithmetic bug" in outcome.note

    def test_right_of_zero_is_empty_not_everything(self):
        assert run('=RIGHT("abc", 0)') == ""

    def test_single_argument_forms_take_one_character(self):
        assert run('=LEFT("abc")') == "a"
        assert run('=RIGHT("abc")') == "c"


class TestTheFamily:
    def test_len_upper_lower_trim(self):
        assert run('=LEN("abc")') == 3.0
        assert run('=UPPER("aBc")') == "ABC"
        assert run('=LOWER("aBc")') == "abc"
        assert run("=TRIM(A1)") == "Quarterly Ledger"

    def test_numbers_render_before_text_functions_touch_them(self):
        assert run("=LEFT(A2, 1)") == "4"
        assert run("=LEN(A2)") == 2.0

    def test_composition_with_the_core_library(self):
        assert run('=IF(LEN("abcd")>3, UPPER("yes"), "no")') == (
            "YES"
        )


class TestTheCatalog:
    def test_both_families_share_one_lookup(self):
        names = catalog()
        assert "SUM" in names
        assert "TRIM" in names
        assert full_table("MID") is not None
        assert full_table("NOPE") is None
