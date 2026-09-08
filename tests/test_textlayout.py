from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.textlayout import (
    center,
    pad_left,
    pad_right,
    wrap_text,
)


class TestWrap:
    def test_it_wraps_at_word_boundaries(self):
        assert wrap_text(
            "the quick brown fox jumps", 10
        ) == ["the quick", "brown fox", "jumps"]

    def test_a_long_word_stays_whole(self):
        assert wrap_text(
            "supercalifragilistic word", 8
        ) == ["supercalifragilistic", "word"]

    def test_runs_of_spaces_collapse(self):
        assert wrap_text("a    b   c", 5) == ["a b c"]

    def test_a_zero_width_is_refused(self):
        with pytest.raises(Invalid):
            wrap_text("hi", 0)


class TestPadding:
    def test_left_and_right(self):
        assert pad_left("hi", 5) == "   hi"
        assert pad_right("hi", 5) == "hi   "

    def test_center_puts_the_odd_space_on_the_right(self):
        assert center("hi", 5) == " hi  "

    def test_center_even(self):
        assert center("hi", 6) == "  hi  "

    def test_padding_never_truncates(self):
        assert pad_left("toolong", 3) == "toolong"
        assert center("toolong", 3) == "toolong"
