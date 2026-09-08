from __future__ import annotations

import pytest

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula


def run(formula: str):
    return evaluate(
        parse_formula(formula), lambda _r: None, full_table
    )


class TestRatioFamilies:
    def test_length(self):
        assert run('=CONVERT(1, "mi", "m")') == 1609.344
        assert run('=CONVERT(1000, "m", "km")') == 1.0
        assert run('=CONVERT(1, "ft", "in")') == (
            pytest.approx(12.0)
        )

    def test_mass(self):
        assert run('=CONVERT(1, "kg", "lbm")') == (
            pytest.approx(2.2046, abs=1e-4)
        )

    def test_time(self):
        assert run('=CONVERT(1, "hr", "min")') == 60.0
        assert run('=CONVERT(1, "day", "hr")') == 24.0


class TestTemperatureIsAffine:
    def test_freezing_is_not_scaled(self):
        assert run('=CONVERT(0, "C", "F")') == (
            pytest.approx(32.0)
        )

    def test_boiling(self):
        assert run('=CONVERT(100, "C", "F")') == (
            pytest.approx(212.0)
        )

    def test_the_reverse_direction(self):
        assert run('=CONVERT(32, "F", "C")') == (
            pytest.approx(0.0, abs=1e-9)
        )

    def test_kelvin_bridges(self):
        assert run('=CONVERT(0, "C", "K")') == (
            pytest.approx(273.15)
        )

    def test_a_ratio_conversion_would_have_broken_this(self):
        # If temperature were scaled like a ratio, 0 C would
        # map to 0 F. The affine offset makes it 32.
        assert run('=CONVERT(0, "C", "F")') != 0.0


class TestRefusals:
    def test_crossing_families_is_refused(self):
        outcome = run('=CONVERT(1, "m", "g")')
        assert outcome.code == "#N/A"
        assert "means nothing" in outcome.note

    def test_an_unknown_unit_is_named(self):
        outcome = run('=CONVERT(1, "smoot", "m")')
        assert outcome.code == "#N/A"
        assert "smoot" in outcome.note

    def test_a_non_text_unit_is_refused(self):
        outcome = run('=CONVERT(1, 5, "m")')
        assert outcome.code == "#VALUE!"
        assert "text abbreviations" in outcome.note

    def test_the_round_trip_is_the_identity(self):
        there = run('=CONVERT(5, "mi", "km")')
        back = evaluate(
            parse_formula(f'=CONVERT({there}, "km", "mi")'),
            lambda _r: None,
            full_table,
        )
        assert back == pytest.approx(5.0)
