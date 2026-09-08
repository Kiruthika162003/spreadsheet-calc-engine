from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.taxbrackets import Bracket, compute_tax

BRACKETS = [
    Bracket(0.0, 0.10),
    Bracket(10000.0, 0.20),
    Bracket(40000.0, 0.30),
]


class TestSlicing:
    def test_income_in_the_first_bracket(self):
        result = compute_tax(5000.0, BRACKETS)
        assert result.total_tax == 500.0
        assert result.marginal_rate == 0.10
        assert result.effective_rate == pytest.approx(0.10)

    def test_income_spanning_two_brackets(self):
        result = compute_tax(25000.0, BRACKETS)
        # 10000 at 10% plus 15000 at 20%.
        assert result.total_tax == 4000.0
        assert result.marginal_rate == 0.20
        assert result.effective_rate == pytest.approx(0.16)

    def test_income_reaching_the_top_bracket(self):
        result = compute_tax(50000.0, BRACKETS)
        assert result.total_tax == 10000.0
        assert result.marginal_rate == 0.30
        assert result.effective_rate == pytest.approx(0.20)


class TestTheDinnerPartyTrap:
    def test_a_raise_taxes_only_the_new_slice(self):
        before = compute_tax(9999.0, BRACKETS)
        after = compute_tax(10001.0, BRACKETS)
        # The two-dollar raise crossing the boundary costs
        # only a few cents more, not a jump on all income.
        extra = after.total_tax - before.total_tax
        assert extra < 1.0

    def test_marginal_and_effective_differ(self):
        result = compute_tax(50000.0, BRACKETS)
        assert result.marginal_rate != result.effective_rate


class TestEdges:
    def test_zero_income_owes_zero_at_zero_rate(self):
        result = compute_tax(0.0, BRACKETS)
        assert result.total_tax == 0.0
        assert result.effective_rate == 0.0

    def test_income_exactly_on_a_threshold(self):
        result = compute_tax(10000.0, BRACKETS)
        assert result.total_tax == 1000.0
        assert result.marginal_rate == 0.10


class TestRefusals:
    def test_an_out_of_order_table_is_refused(self):
        bad = [Bracket(0.0, 0.1), Bracket(5000.0, 0.2), Bracket(3000.0, 0.3)]
        with pytest.raises(Invalid) as caught:
            compute_tax(10000.0, bad)
        assert "does not rise" in str(caught.value)

    def test_a_table_not_starting_at_zero(self):
        bad = [Bracket(1000.0, 0.1)]
        with pytest.raises(Invalid) as caught:
            compute_tax(5000.0, bad)
        assert "start at zero" in str(caught.value)

    def test_a_rate_over_one_is_a_typo(self):
        bad = [Bracket(0.0, 1.1)]
        with pytest.raises(Invalid) as caught:
            compute_tax(5000.0, bad)
        assert "not a policy" in str(caught.value)

    def test_negative_income_is_refused(self):
        with pytest.raises(Invalid):
            compute_tax(-100.0, BRACKETS)
