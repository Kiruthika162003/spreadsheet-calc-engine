from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.richtext import RichText


class TestThePlainTextInvariant:
    def test_plain_text_survives_styling(self):
        rich = RichText.plain("hello world")
        rich.apply(0, 5, bold=True)
        assert rich.text() == "hello world"

    def test_a_styled_middle_splits_into_three_runs(self):
        rich = RichText.plain("hello world")
        rich.apply(6, 11, color="red")
        assert rich.run_count() == 2
        assert rich.text() == "hello world"

    def test_styling_the_interior_makes_three(self):
        rich = RichText.plain("abcdef")
        rich.apply(2, 4, italic=True)
        assert rich.run_count() == 3
        assert [r.text for r in rich.runs] == [
            "ab",
            "cd",
            "ef",
        ]


class TestMerging:
    def test_bold_then_unbold_returns_to_one_run(self):
        rich = RichText.plain("abcdef")
        rich.apply(2, 4, bold=True)
        assert rich.run_count() == 3
        rich.apply(2, 4, bold=False)
        assert rich.run_count() == 1
        assert rich.runs[0].bold is False

    def test_adjacent_identical_runs_merge(self):
        rich = RichText.plain("abcdef")
        rich.apply(0, 3, bold=True)
        rich.apply(3, 6, bold=True)
        assert rich.run_count() == 1

    def test_overlapping_applications_compose(self):
        rich = RichText.plain("abcdef")
        rich.apply(0, 4, bold=True)
        rich.apply(2, 6, italic=True)
        # Expect: ab bold, cd bold+italic, ef italic.
        assert rich.run_count() == 3
        assert rich.text() == "abcdef"


class TestRefusals:
    def test_a_range_past_the_end_is_refused(self):
        rich = RichText.plain("abc")
        with pytest.raises(Invalid) as caught:
            rich.apply(0, 9, bold=True)
        assert "do not exist" in str(caught.value)

    def test_an_inverted_range_is_refused(self):
        rich = RichText.plain("abc")
        with pytest.raises(Invalid):
            rich.apply(2, 1, bold=True)

    def test_empty_plain_has_no_runs(self):
        assert RichText.plain("").run_count() == 0
