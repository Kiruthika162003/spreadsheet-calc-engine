from __future__ import annotations

import pytest

from gridiron.autofill import plan_fill
from gridiron.errors import Invalid


class TestNumbers:
    def test_an_arithmetic_series_continues(self):
        plan = plan_fill([2.0, 4.0, 6.0], 3)
        assert plan.values == (8.0, 10.0, 12.0)
        assert "step 2" in plan.pattern

    def test_a_descending_series_descends(self):
        plan = plan_fill([10.0, 7.0], 2)
        assert plan.values == (4.0, 1.0)

    def test_a_lone_number_repeats_not_counts(self):
        plan = plan_fill([5.0], 3)
        assert plan.values == (5.0, 5.0, 5.0)
        assert "repetition" in plan.pattern

    def test_equal_seeds_are_constant_repetition(self):
        plan = plan_fill([3.0, 3.0], 2)
        assert plan.values == (3.0, 3.0)
        assert plan.pattern == "constant repetition"

    def test_no_constant_difference_refuses(self):
        with pytest.raises(Invalid) as caught:
            plan_fill([1.0, 2.0, 4.0], 2)
        assert "lying about having inferred" in str(
            caught.value
        )


class TestCycles:
    def test_weekdays_wrap_like_calendars(self):
        plan = plan_fill(["Fri", "Sat"], 3)
        assert plan.values == ("Sun", "Mon", "Tue")
        assert "short weekdays" in plan.pattern

    def test_months_rotate_with_a_stride(self):
        plan = plan_fill(["Jan", "Apr"], 3)
        assert plan.values == ("Jul", "Oct", "Jan")

    def test_one_seed_steps_by_one(self):
        plan = plan_fill(["Wednesday"], 2)
        assert plan.values == ("Thursday", "Friday")
        assert "long weekdays" in plan.pattern

    def test_the_seed_case_is_matched(self):
        assert plan_fill(["MON"], 1).values == ("TUE",)
        assert plan_fill(["mon"], 1).values == ("tue",)
        assert plan_fill(["Mon"], 1).values == ("Tue",)


class TestStems:
    def test_a_numbered_stem_advances(self):
        plan = plan_fill(["Item 1", "Item 2"], 3)
        assert plan.values == (
            "Item 3",
            "Item 4",
            "Item 5",
        )

    def test_a_lone_stem_counts_upward(self):
        plan = plan_fill(["Q3"], 2)
        assert plan.values == ("Q4", "Q5")

    def test_stems_that_disagree_refuse(self):
        with pytest.raises(Invalid) as caught:
            plan_fill(["Item 1", "Box 2"], 2)
        assert "average two ideas" in str(caught.value)

    def test_a_stem_stride_is_kept(self):
        plan = plan_fill(["Row 10", "Row 20"], 2)
        assert plan.values == ("Row 30", "Row 40")


class TestRefusals:
    def test_plain_text_repeats_only_when_uniform(self):
        plan = plan_fill(["total", "total"], 2)
        assert plan.values == ("total", "total")

    def test_unrelated_labels_refuse_by_name(self):
        with pytest.raises(Invalid) as caught:
            plan_fill(["alpha", "omega"], 2)
        assert "no rung of the ladder" in str(caught.value)

    def test_mixed_kinds_refuse(self):
        with pytest.raises(Invalid) as caught:
            plan_fill([1.0, "two"], 2)
        assert "mix kinds" in str(caught.value)

    def test_the_verdict_previews_the_guess(self):
        verdict = plan_fill([2.0, 4.0], 5).verdict()
        assert verdict.startswith(
            "arithmetic series, step 2: 6, 8, 10..."
        )
