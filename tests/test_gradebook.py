from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.gradebook import (
    Category,
    course_percentage,
    letter_grade,
)


class TestWeighting:
    def test_a_weighted_course_grade(self):
        cats = [
            Category("HW", 0.4, [80.0, 90.0, 100.0]),
            Category("Exam", 0.6, [85.0, 95.0]),
        ]
        assert course_percentage(cats) == pytest.approx(90.0)

    def test_weights_must_sum_to_one(self):
        cats = [
            Category("HW", 0.4, [90.0]),
            Category("Exam", 0.5, [90.0]),
        ]
        with pytest.raises(Invalid) as caught:
            course_percentage(cats)
        assert "wrong denominator" in str(caught.value)


class TestDropLowest:
    def test_the_lowest_score_is_dropped(self):
        cat = Category(
            "HW", 1.0, [90.0, 80.0, 100.0, 70.0], drop_lowest=1
        )
        assert cat.average() == pytest.approx(90.0)

    def test_dropping_too_many_is_refused(self):
        cat = Category("HW", 1.0, [90.0], drop_lowest=1)
        with pytest.raises(Invalid) as caught:
            cat.average()
        assert "empty by policy" in str(caught.value)


class TestIncompleteCategories:
    def test_an_empty_category_renormalizes(self):
        cats = [
            Category("HW", 0.4, [100.0]),
            Category("Exam", 0.6, []),
        ]
        # Only HW is graded; the grade reflects it alone.
        assert course_percentage(cats) == 100.0

    def test_all_empty_has_no_grade(self):
        cats = [
            Category("HW", 0.4, []),
            Category("Exam", 0.6, []),
        ]
        with pytest.raises(Invalid) as caught:
            course_percentage(cats)
        assert "no grade to compute" in str(caught.value)


class TestLetterGrade:
    def test_the_thresholds(self):
        assert letter_grade(95.0) == "A"
        assert letter_grade(85.0) == "B"
        assert letter_grade(50.0) == "F"

    def test_a_boundary_earns_the_higher_letter(self):
        assert letter_grade(90.0) == "A"
        assert letter_grade(80.0) == "B"
