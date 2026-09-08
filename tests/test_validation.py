from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.validation import Validator


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def guarded() -> Validator:
    validator = Validator(sheet=Sheet())
    validator.add_list_rule(
        RangeRef.parse("A1:A9"),
        allowed=("open", "closed", "pending"),
    )
    validator.add_range_rule(
        RangeRef.parse("B1:B9"), low=0.0, high=100.0
    )
    return validator


class TestTheDoor:
    def test_permitted_values_land(self):
        validator = guarded()
        validator.set_literal(ref("A1"), "open")
        validator.set_literal(ref("B1"), 55.0)
        assert validator.sheet.value_of(ref("B1")) == 55.0

    def test_the_rejection_quotes_the_rule(self):
        validator = guarded()
        with pytest.raises(Invalid) as caught:
            validator.set_literal(ref("A1"), "maybe")
        assert "one of open, closed, pending" in str(
            caught.value
        )
        assert "teaches the constraint" in str(caught.value)

    def test_range_rules_bound_numbers_only(self):
        validator = guarded()
        with pytest.raises(Invalid):
            validator.set_literal(ref("B1"), 250.0)
        with pytest.raises(Invalid):
            validator.set_literal(ref("B1"), "high")

    def test_cells_outside_every_rule_are_free(self):
        validator = guarded()
        validator.set_literal(ref("Z9"), "anything")

    def test_custom_rules_ride_the_criteria_language(self):
        validator = Validator(sheet=Sheet())
        validator.add_custom_rule(
            RangeRef.parse("C1:C3"), ">=10"
        )
        validator.set_literal(ref("C1"), 15.0)
        with pytest.raises(Invalid):
            validator.set_literal(ref("C2"), 5.0)


class TestTheAudit:
    def test_pre_existing_violations_are_named(self):
        validator = Validator(sheet=Sheet())
        validator.sheet.set_literal(ref("B2"), 250.0)
        validator.add_range_rule(
            RangeRef.parse("B1:B9"), low=0.0, high=100.0
        )
        audit = validator.audit()
        assert "1 pre-existing violation(s)" in audit
        assert "B2 holds '250' against between 0.0 and 100.0" in (
            audit
        )
        assert "a lie the sheet tells forever" in audit

    def test_the_clean_room_says_so(self):
        validator = guarded()
        validator.set_literal(ref("A1"), "open")
        assert "the room was clean before the door was" in (
            validator.audit()
        )

    def test_formulas_bypass_by_design(self):
        validator = guarded()
        validator.sheet.set_formula(ref("B3"), "=999")
        assert "clean" in validator.audit()

    def test_backwards_bounds_are_refused(self):
        with pytest.raises(Invalid):
            Validator(sheet=Sheet()).add_range_rule(
                RangeRef.parse("A1:A2"), low=9.0, high=1.0
            )
