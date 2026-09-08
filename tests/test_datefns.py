from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef


def lookup(_ref: CellRef):
    return None


def run(formula: str):
    return evaluate(
        parse_formula(formula), lookup, full_table
    )


class TestDate:
    def test_date_builds_a_serial_and_parts_recover_it(self):
        serial = run("=DATE(2024, 3, 15)")
        assert run(f"=YEAR({serial})") == 2024.0
        assert run(f"=MONTH({serial})") == 3.0
        assert run(f"=DAY({serial})") == 15.0

    def test_the_impossible_date_is_refused_not_normalized(self):
        outcome = run("=DATE(2024, 2, 30)")
        assert outcome.code == "#NUM!"
        assert "bury the bug that produced it" in outcome.note

    def test_date_arithmetic_in_a_formula(self):
        assert run(
            "=DATE(2024, 3, 15) - DATE(2024, 3, 1)"
        ) == 14.0


class TestEdate:
    def test_the_plain_shift_keeps_the_day(self):
        serial = run("=EDATE(DATE(2024, 1, 15), 1)")
        assert run(f"=MONTH({serial})") == 2.0
        assert run(f"=DAY({serial})") == 15.0

    def test_the_clamp_is_stated_behavior(self):
        serial = run("=EDATE(DATE(2024, 1, 31), 1)")
        assert run(f"=MONTH({serial})") == 2.0
        assert run(f"=DAY({serial})") == 29.0

    def test_negative_shifts_walk_backwards(self):
        serial = run("=EDATE(DATE(2024, 3, 31), 0-1)")
        assert run(f"=MONTH({serial})") == 2.0
        assert run(f"=DAY({serial})") == 29.0


class TestNetworkdays:
    def test_both_fenceposts_count(self):
        assert run(
            "=NETWORKDAYS(DATE(2024,3,4), DATE(2024,3,8))"
        ) == 5.0

    def test_weekends_vanish(self):
        assert run(
            "=NETWORKDAYS(DATE(2024,3,4), DATE(2024,3,11))"
        ) == 6.0

    def test_the_backwards_interval_is_named(self):
        outcome = run(
            "=NETWORKDAYS(DATE(2024,3,8), DATE(2024,3,4))"
        )
        assert outcome.code == "#NUM!"
        assert "swap them deliberately" in outcome.note
