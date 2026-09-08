"""Conditional formatting: rules with precedence, and a stop that means stop.

A conditional format is a criterion wearing a style, and the
part that bites is ordering: several rules can match one
cell, they apply in declared priority, and a rule marked
stop-if-true ends the cascade for that cell, which is the
mechanism behind every "red overrides yellow" convention on
every dashboard. This module evaluates rules against values
and returns style names, never touching storage, because
formatting that writes to cells is how display bugs become
data bugs. The census answers the two questions rule sets
accumulate toward: which rules currently match nothing, dead
weight worth deleting, and which cells match three or more
rules, ambiguity worth simplifying, since a cell with five
competing formats is a debate the reader loses.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.criteria import Criterion
from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet


@dataclass(frozen=True)
class FormatRule:
    priority: int
    region: RangeRef
    criterion: Criterion
    style: str
    stop_if_true: bool = False


@dataclass
class ConditionalFormats:
    sheet: Sheet
    rules: list[FormatRule] = field(default_factory=list)

    def add_rule(
        self,
        priority: int,
        region: RangeRef,
        criterion_text: str,
        style: str,
        stop_if_true: bool = False,
    ) -> None:
        if not style.strip():
            raise Invalid("a rule needs a style to apply")
        if any(
            rule.priority == priority for rule in self.rules
        ):
            raise Invalid(
                f"priority {priority} is taken; ties would "
                "make the cascade order a coin flip"
            )
        self.rules.append(
            FormatRule(
                priority=priority,
                region=region,
                criterion=Criterion.parse(criterion_text),
                style=style,
                stop_if_true=stop_if_true,
            )
        )
        self.rules.sort(key=lambda rule: rule.priority)

    def styles_for(self, ref: CellRef) -> list[str]:
        value = self.sheet.value_of(ref)
        applied: list[str] = []
        for rule in self.rules:
            if not rule.region.contains(ref):
                continue
            if rule.criterion.matches(value):
                applied.append(rule.style)
                if rule.stop_if_true:
                    break
        return applied

    def census(self) -> str:
        matched_by_rule = {
            rule.priority: 0 for rule in self.rules
        }
        crowded: list[str] = []
        probed: set[tuple[int, int]] = set()
        for rule in self.rules:
            for cell in rule.region.cells():
                probed.add(cell.key())
        for key in sorted(probed):
            ref = CellRef(row=key[0], col=key[1])
            value = self.sheet.value_of(ref)
            hits = [
                rule
                for rule in self.rules
                if rule.region.contains(ref)
                and rule.criterion.matches(value)
            ]
            for rule in hits:
                matched_by_rule[rule.priority] += 1
            if len(hits) >= 3:
                crowded.append(
                    f"{ref.a1()} matches {len(hits)} rules"
                )
        dead = [
            f"priority {priority}"
            for priority, count in matched_by_rule.items()
            if count == 0
        ]
        lines = []
        if dead:
            lines.append(
                f"dead weight: {', '.join(dead)} match "
                "nothing and are worth deleting"
            )
        if crowded:
            lines.append(
                f"ambiguity: {'; '.join(crowded)}; a cell "
                "with competing formats is a debate the "
                "reader loses"
            )
        if not lines:
            return "every rule earns its place"
        return "\n".join(lines)
