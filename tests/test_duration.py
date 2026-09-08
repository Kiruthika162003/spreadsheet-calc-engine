from __future__ import annotations

import pytest

from gridiron.duration import format_duration, parse_duration
from gridiron.errors import Invalid


class TestFormat:
    def test_it_shows_only_nonzero_units(self):
        assert format_duration(90) == "1m 30s"
        assert format_duration(45) == "45s"

    def test_the_full_ladder(self):
        assert format_duration(90061) == "1d 1h 1m 1s"

    def test_zero_is_shown(self):
        assert format_duration(0) == "0s"

    def test_a_negative_is_refused(self):
        with pytest.raises(Invalid) as caught:
            format_duration(-5)
        assert "subtraction that escaped" in str(
            caught.value
        )


class TestParse:
    def test_it_reads_back(self):
        assert parse_duration("1h 1m 1s") == 3661
        assert parse_duration("45s") == 45

    def test_an_unknown_unit_is_refused(self):
        with pytest.raises(Invalid) as caught:
            parse_duration("1h 30x")
        assert "silently lose" in str(caught.value)

    def test_a_repeated_unit_is_refused(self):
        with pytest.raises(Invalid) as caught:
            parse_duration("1h 2h")
        assert "appears twice" in str(caught.value)

    def test_a_malformed_piece_is_refused(self):
        with pytest.raises(Invalid):
            parse_duration("abc")


class TestRoundTrip:
    def test_every_span_survives(self):
        failures = [
            s
            for s in range(0, 100000, 13)
            if parse_duration(format_duration(s)) != s
        ]
        assert failures == []
