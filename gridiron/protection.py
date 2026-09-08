"""Sheet protection: locked ranges, named exceptions, and an unlock that expires.

Protection is not security, it is a guardrail, and the
module says so up front: anyone with the workbook can lift
it, the point is preventing the accidental Tuesday edit of
the January totals, not stopping an attacker. Locked ranges
refuse edits with the range's registered reason, because
"locked: closed period, see finance" converts an obstacle
into an explanation. Exceptions are named unlocked ranges
punched through a lock, the input cells inside a protected
model, and the unlock-all is deliberately temporary: it
takes an edit budget and relocks after that many edits, so
the escape hatch cannot quietly become the permanent state,
which is the fate of every unlock that trusts someone to
remember to relock.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef


@dataclass
class Protection:
    locks: list[tuple[RangeRef, str]] = field(
        default_factory=list
    )
    exceptions: list[RangeRef] = field(default_factory=list)
    unlocked_edits_left: int = 0

    def lock(self, region: RangeRef, reason: str) -> str:
        if not reason.strip():
            raise Invalid(
                "a lock without a reason is an obstacle; "
                "with one it is an explanation"
            )
        self.locks.append((region, reason))
        return f"{region.a1()} locked: {reason}"

    def punch_exception(self, region: RangeRef) -> str:
        if not any(
            lock.contains(CellRef(row=region.top, col=region.left))
            for lock, _ in self.locks
        ):
            raise Invalid(
                f"{region.a1()} is not inside any lock; an "
                "exception needs something to except from"
            )
        self.exceptions.append(region)
        return (
            f"{region.a1()} punched through as input cells"
        )

    def check_edit(self, ref: CellRef) -> None:
        if self.unlocked_edits_left > 0:
            self.unlocked_edits_left -= 1
            return
        for region in self.exceptions:
            if region.contains(ref):
                return
        for region, reason in self.locks:
            if region.contains(ref):
                raise Invalid(
                    f"{ref.a1()} is locked: {reason}"
                )

    def unlock_all(self, edit_budget: int) -> str:
        if edit_budget < 1:
            raise Invalid("the unlock needs an edit budget")
        self.unlocked_edits_left = edit_budget
        return (
            f"unlocked for {edit_budget} edit(s), then the "
            "locks return on their own, because every unlock "
            "that trusts someone to remember becomes the "
            "permanent state"
        )

    def census(self) -> str:
        if not self.locks:
            return "nothing locked; every cell is a Tuesday risk"
        lines = [f"{len(self.locks)} lock(s):"]
        for region, reason in self.locks:
            lines.append(f"  {region.a1()}: {reason}")
        for region in self.exceptions:
            lines.append(
                f"  except {region.a1()}: input cells"
            )
        return "\n".join(lines)
