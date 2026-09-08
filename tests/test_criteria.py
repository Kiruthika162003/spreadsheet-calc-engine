from __future__ import annotations

import pytest

from gridiron.criteria import Criterion
from gridiron.errors import Invalid


class TestNumericCriteria:
    def test_the_comparison_family(self):
        assert Criterion.parse(">100").matches(150.0)
        assert not Criterion.parse(">100").matches(100.0)
        assert Criterion.parse("<=5").matches(5.0)
        assert Criterion.parse("<>3").matches(4.0)
        assert Criterion.parse("42").matches(42.0)

    def test_text_never_satisfies_a_numeric_comparison(self):
        assert not Criterion.parse(">100").matches("150")
        assert Criterion.parse("<>100").matches("anything")

    def test_booleans_are_not_numbers_here(self):
        assert not Criterion.parse(">0").matches(True)


class TestTextCriteria:
    def test_bare_text_means_equals_case_folded(self):
        assert Criterion.parse("done").matches("DONE")
        assert not Criterion.parse("done").matches("pending")

    def test_not_equals_reads_naturally(self):
        assert Criterion.parse("<>done").matches("pending")
        assert not Criterion.parse("<>done").matches("Done")

    def test_numbers_never_satisfy_text_equality(self):
        assert not Criterion.parse("done").matches(42.0)


class TestWildcards:
    def test_star_and_question_compile(self):
        assert Criterion.parse("app*").matches("apples")
        assert Criterion.parse("app*").matches("APP")
        assert Criterion.parse("gr?y").matches("gray")
        assert Criterion.parse("gr?y").matches("grey")
        assert not Criterion.parse("gr?y").matches("graay")

    def test_wildcards_negate_with_not_equals(self):
        assert Criterion.parse("<>app*").matches("bread")
        assert not Criterion.parse("<>app*").matches("apples")

    def test_wildcards_refuse_ordering_operators(self):
        with pytest.raises(Invalid) as caught:
            Criterion.parse(">app*")
        assert "only combine with = or <>" in str(caught.value)


class TestRefusals:
    def test_the_empty_criterion_wants_isblank(self):
        with pytest.raises(Invalid) as caught:
            Criterion.parse("")
        assert "explicit ISBLANK" in str(caught.value)

    def test_ordering_against_text_is_refused(self):
        with pytest.raises(Invalid):
            Criterion.parse(">=done")
