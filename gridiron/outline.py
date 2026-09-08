"""Row outlines: groups that nest or stay apart, never braid.

An outline is a set of row groups with one structural law:
two groups are either disjoint or one contains the other,
because a group that partially overlaps another braids the
outline and no collapse order can untangle it, so the braid
is refused at creation instead of detonating at collapse.
Collapsing hides every row of the group including its nested
children's rows, while the children remember their own
collapsed state for when the parent opens again, which is
why hiding is computed from the tree at read time rather
than stored as a flat set that would forget the nesting. The
level of a row is how many groups contain it, the census
reports groups, depth, and hidden rows in one line, and the
hidden set is exported in exactly the shape the subtotal
scope adopts, so a SUBTOTAL over a collapsed outline sums
the visible story, which is the entire reason outlines and
subtotals ship as a pair in every grid that has them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid, Missing


@dataclass
class Group:
    start: int
    end: int
    collapsed: bool = False

    def contains(self, other: Group) -> bool:
        return (
            self.start <= other.start
            and other.end <= self.end
        )

    def disjoint(self, other: Group) -> bool:
        return (
            self.end < other.start
            or other.end < self.start
        )

    def covers(self, row: int) -> bool:
        return self.start <= row <= self.end

    def span(self) -> str:
        return f"rows {self.start + 1}-{self.end + 1}"


@dataclass
class Outline:
    groups: list[Group] = field(default_factory=list)

    def group_rows(self, start: int, end: int) -> str:
        if start > end or start < 0:
            raise Invalid(
                f"rows {start + 1}-{end + 1} do not make "
                "a group"
            )
        candidate = Group(start=start, end=end)
        for existing in self.groups:
            if (
                existing.start == start
                and existing.end == end
            ):
                raise Invalid(
                    f"the group {candidate.span()} already "
                    "exists"
                )
            legal = (
                existing.disjoint(candidate)
                or existing.contains(candidate)
                or candidate.contains(existing)
            )
            if not legal:
                raise Invalid(
                    f"{candidate.span()} partially overlaps "
                    f"{existing.span()}; braided groups "
                    "cannot be untangled by any collapse "
                    "order"
                )
        self.groups.append(candidate)
        return f"grouped {candidate.span()}"

    def _find(self, start: int, end: int) -> Group:
        for group in self.groups:
            if group.start == start and group.end == end:
                return group
        raise Missing(
            f"no group spans rows {start + 1}-{end + 1}"
        )

    def collapse(self, start: int, end: int) -> str:
        group = self._find(start, end)
        if group.collapsed:
            return f"{group.span()} was already collapsed"
        group.collapsed = True
        return (
            f"collapsed {group.span()}; "
            f"{len(self.hidden_rows())} row(s) now hidden"
        )

    def expand(self, start: int, end: int) -> str:
        group = self._find(start, end)
        if not group.collapsed:
            return f"{group.span()} was already open"
        group.collapsed = False
        return (
            f"expanded {group.span()}; nested groups keep "
            "their own state"
        )

    def hidden_rows(self) -> set[int]:
        hidden: set[int] = set()
        for group in self.groups:
            if group.collapsed:
                hidden.update(
                    range(group.start, group.end + 1)
                )
        return hidden

    def level_of(self, row: int) -> int:
        return sum(
            1 for group in self.groups if group.covers(row)
        )

    def visible_rows(
        self, top: int, bottom: int
    ) -> list[int]:
        hidden = self.hidden_rows()
        return [
            row
            for row in range(top, bottom + 1)
            if row not in hidden
        ]

    def census(self) -> str:
        depth = max(
            (
                self.level_of(row)
                for group in self.groups
                for row in (group.start,)
            ),
            default=0,
        )
        return (
            f"{len(self.groups)} group(s), max depth "
            f"{depth}, {len(self.hidden_rows())} row(s) "
            "hidden"
        )
