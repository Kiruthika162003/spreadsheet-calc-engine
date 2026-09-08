"""AST nodes: the formula's shape, with every reference discoverable.

The tree is deliberately small, eight node kinds, because
every kind is a case somewhere downstream: the evaluator
matches on all of them, the reference walker matches on all
of them, and the paste rewriter matches on all of them, so
each new kind is a tax on three walkers. The one method every
node shares is refs(), which yields the cell and range
references underneath it, because the dependency graph is
built from exactly that walk and a node that hid a reference
from refs() would be a formula the recalculator cannot see,
the quietest possible corruption.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.refs import CellRef, RangeRef


@dataclass(frozen=True)
class Number:
    value: float

    def refs(self) -> list[CellRef | RangeRef]:
        return []


@dataclass(frozen=True)
class Text:
    value: str

    def refs(self) -> list[CellRef | RangeRef]:
        return []


@dataclass(frozen=True)
class Bool:
    value: bool

    def refs(self) -> list[CellRef | RangeRef]:
        return []


@dataclass(frozen=True)
class Ref:
    ref: CellRef

    def refs(self) -> list[CellRef | RangeRef]:
        return [self.ref]


@dataclass(frozen=True)
class Range:
    ref: RangeRef

    def refs(self) -> list[CellRef | RangeRef]:
        return [self.ref]


@dataclass(frozen=True)
class Name:
    name: str

    def refs(self) -> list[CellRef | RangeRef]:
        return []


@dataclass(frozen=True)
class Unary:
    op: str
    operand: Node

    def refs(self) -> list[CellRef | RangeRef]:
        return self.operand.refs()


@dataclass(frozen=True)
class Binary:
    op: str
    left: Node
    right: Node

    def refs(self) -> list[CellRef | RangeRef]:
        return [*self.left.refs(), *self.right.refs()]


@dataclass(frozen=True)
class Call:
    function: str
    args: tuple[Node, ...]

    def refs(self) -> list[CellRef | RangeRef]:
        found: list[CellRef | RangeRef] = []
        for arg in self.args:
            found.extend(arg.refs())
        return found


Node = (
    Number | Text | Bool | Ref | Range | Name | Unary | Binary | Call
)
