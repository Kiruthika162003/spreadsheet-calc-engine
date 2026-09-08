from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula


def run(formula: str):
    return evaluate(
        parse_formula(formula), lambda _r: None, full_table
    )


class TestToBase:
    def test_positive_conversions(self):
        assert run("=DEC2BIN(5)") == "101"
        assert run("=DEC2OCT(64)") == "100"
        assert run("=DEC2HEX(255)") == "FF"

    def test_zero_is_a_single_digit(self):
        assert run("=DEC2BIN(0)") == "0"

    def test_negative_one_is_ten_ones(self):
        assert run("=DEC2BIN(-1)") == "1111111111"

    def test_the_ten_bit_range_is_enforced(self):
        outcome = run("=DEC2BIN(512)")
        assert outcome.code == "#NUM!"
        assert "-512 to 511" in outcome.note

    def test_the_low_end_is_reachable(self):
        assert run("=DEC2BIN(-512)") == "1000000000"


class TestFromBase:
    def test_positive_round_trip(self):
        assert run('=BIN2DEC("101")') == 5.0
        assert run('=HEX2DEC("FF")') == 255.0
        assert run('=OCT2DEC("100")') == 64.0

    def test_the_sign_bit_is_read_back(self):
        assert run('=BIN2DEC("1111111111")') == -1.0

    def test_a_short_string_is_positive(self):
        assert run('=BIN2DEC("111")') == 7.0

    def test_a_foreign_digit_is_refused(self):
        outcome = run('=BIN2DEC("102")')
        assert outcome.code == "#NUM!"
        assert "looks right" in outcome.note

    def test_a_hex_letter_out_of_range_for_octal(self):
        outcome = run('=OCT2DEC("8")')
        assert outcome.code == "#NUM!"


class TestBitwise:
    def test_the_three_operators(self):
        assert run("=BITAND(12, 10)") == 8.0
        assert run("=BITOR(12, 10)") == 14.0
        assert run("=BITXOR(12, 10)") == 6.0

    def test_a_negative_operand_is_refused(self):
        outcome = run("=BITAND(-1, 3)")
        assert outcome.code == "#NUM!"
        assert "non-negative" in outcome.note

    def test_a_fractional_operand_is_refused(self):
        outcome = run("=BITOR(2.5, 1)")
        assert outcome.code == "#NUM!"
        assert "whole number" in outcome.note


class TestTheRoundTripLaw:
    def test_every_value_survives_the_round_trip(self):
        for number in (-512, -1, 0, 1, 42, 511):
            text = run(f"=DEC2BIN({number})")
            back = evaluate(
                parse_formula(f'=BIN2DEC("{text}")'),
                lambda _r: None,
                full_table,
            )
            assert back == float(number)
