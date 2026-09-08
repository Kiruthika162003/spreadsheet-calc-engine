"""Data validation: the gate at entry, with an audit for what got in before.

Validation guards the door: a rule bound to a range vets
every literal before it lands, list rules against their
allowed values, range rules against their bounds, and custom
rules through a criterion, with the rejection quoting the
rule so the user learns the constraint instead of fighting
it. The half most engines skip is the retroactive audit:
rules arrive after data constantly, and a rule that only
guards the door certifies a room full of strangers. The
audit walks existing cells under each rule and names every
violation with its cell and value, because "B7 holds 250
against a max of 100" is a cleanup task while a silent
pre-existing violation is a lie the sheet tells forever.
Formulas bypass validation by design and the docstring says
so: validation vets what people type, and what formulas
compute is the engine's business, checked by other means.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.criteria import Criterion
from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import Value, render


@dataclass(frozen=True)
class Rule:
    kind: str
    region: RangeRef
    allowed: tuple[str, ...] = ()
    low: float | None = None
    high: float | None = None
    criterion: Criterion | None = None

    def describe(self) -> str:
        if self.kind == "list":
            return f"one of {', '.join(self.allowed)}"
        if self.kind == "range":
            return f"between {self.low} and {self.high}"
        return f"matching {self.criterion.source!r}"

    def permits(self, value: Value) -> bool:
        if self.kind == "list":
            return (
                isinstance(value, str)
                and value in self.allowed
            )
        if self.kind == "range":
            return (
                isinstance(value, float)
                and not isinstance(value, bool)
                and self.low <= value <= self.high
            )
        return self.criterion.matches(value)


@dataclass
class Validator:
    sheet: Sheet
    rules: list[Rule] = field(default_factory=list)

    def add_list_rule(
        self, region: RangeRef, allowed: tuple[str, ...]
    ) -> None:
        if not allowed:
            raise Invalid("a list rule needs allowed values")
        self.rules.append(
            Rule(kind="list", region=region, allowed=allowed)
        )

    def add_range_rule(
        self, region: RangeRef, low: float, high: float
    ) -> None:
        if low > high:
            raise Invalid("the bounds are backwards")
        self.rules.append(
            Rule(
                kind="range",
                region=region,
                low=low,
                high=high,
            )
        )

    def add_custom_rule(
        self, region: RangeRef, criterion_text: str
    ) -> None:
        self.rules.append(
            Rule(
                kind="custom",
                region=region,
                criterion=Criterion.parse(criterion_text),
            )
        )

    def set_literal(self, ref: CellRef, value: Value) -> None:
        for rule in self.rules:
            if rule.region.contains(ref) and not rule.permits(
                value
            ):
                raise Invalid(
                    f"{ref.a1()} rejects {render(value)!r}: "
                    f"the rule wants {rule.describe()}, and "
                    "quoting it teaches the constraint "
                    "instead of fighting it"
                )
        self.sheet.set_literal(ref, value)

    def audit(self) -> str:
        violations = []
        for rule in self.rules:
            for cell_ref in rule.region.cells():
                held = self.sheet.cell(cell_ref)
                if held is None or held.is_formula():
                    continue
                if not rule.permits(held.literal):
                    violations.append(
                        f"{cell_ref.a1()} holds "
                        f"{render(held.literal)!r} against "
                        f"{rule.describe()}"
                    )
        if not violations:
            return (
                "every existing value satisfies its rules; "
                "the room was clean before the door was"
            )
        lines = [
            f"{len(violations)} pre-existing violation(s), "
            "named because a silent one is a lie the sheet "
            "tells forever:"
        ]
        lines.extend(f"  {entry}" for entry in violations)
        return "\n".join(lines)
