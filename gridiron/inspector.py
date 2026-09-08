"""The inspector: a workbook's shape, measured before it becomes folklore.

Every aging workbook grows a reputation, "the big one is
slow, do not touch column Q", and the inspector replaces the
folklore with numbers: the deepest dependency chain, because
depth bounds how long an edit's ripple can take; the widest
fan-in, the cell most formulas watch, because that cell is
the workbook's load-bearing wall; the formula complexity
census by node count, because a formula with ninety nodes is
a program wearing a cell's clothes and deserves a name and a
test; and the error census, every cell currently showing an
error code, because errors people have scrolled past are
still errors. Each number names its cell, since a statistic
without an address is a worry, and a statistic with one is a
task.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.ast import Binary, Call, Node, Unary
from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.values import is_error


def node_count(tree: Node) -> int:
    if isinstance(tree, Unary):
        return 1 + node_count(tree.operand)
    if isinstance(tree, Binary):
        return (
            1
            + node_count(tree.left)
            + node_count(tree.right)
        )
    if isinstance(tree, Call):
        return 1 + sum(
            node_count(arg) for arg in tree.args
        )
    return 1


COMPLEXITY_ALARM = 25


@dataclass
class Inspector:
    engine: Engine

    def deepest_chain(self) -> str:
        self.engine._reindex()
        depths: dict[tuple[int, int], int] = {}

        def depth_of(key: tuple[int, int]) -> int:
            if key in depths:
                return depths[key]
            depths[key] = 0
            cell = self.engine.sheet.cells.get(key)
            if cell is None or not cell.is_formula():
                return 0
            best = 0
            for precedent in cell.tree.refs():
                if isinstance(precedent, CellRef):
                    best = max(
                        best, depth_of(precedent.key())
                    )
                else:
                    for member in precedent.cells():
                        if (
                            member.key()
                            in self.engine.sheet.cells
                        ):
                            best = max(
                                best,
                                depth_of(member.key()),
                            )
            depths[key] = best + 1
            return depths[key]

        formula_cells = self.engine.sheet.formula_cells()
        if not formula_cells:
            raise Invalid("no formulas; the workbook is a table")
        winner = max(
            formula_cells,
            key=lambda pair: depth_of(pair[0].key()),
        )
        depth = depths[winner[0].key()]
        return (
            f"deepest chain: {depth} link(s) ending at "
            f"{winner[0].a1()}; depth bounds how long an "
            "edit's ripple can take"
        )

    def load_bearing_wall(self) -> str:
        self.engine._reindex()
        counts: dict[tuple[int, int], int] = {}
        for key, dependents in (
            self.engine.cell_dependents.items()
        ):
            counts[key] = len(dependents)
        for region, _ in self.engine.range_watchers:
            for member in region.cells():
                if member.key() in self.engine.sheet.cells:
                    counts[member.key()] = (
                        counts.get(member.key(), 0) + 1
                    )
        if not counts:
            raise Invalid("nothing watches anything")
        key, watchers = max(
            counts.items(), key=lambda pair: pair[1]
        )
        wall = CellRef(row=key[0], col=key[1])
        return (
            f"load-bearing wall: {wall.a1()} with "
            f"{watchers} watcher(s); edits here ripple "
            "furthest"
        )

    def complexity_alarms(self) -> list[str]:
        found = []
        for ref, cell in self.engine.sheet.formula_cells():
            count = node_count(cell.tree)
            if count > COMPLEXITY_ALARM:
                found.append(
                    f"{ref.a1()}: {count} nodes; a program "
                    "wearing a cell's clothes deserves a "
                    "name and a test"
                )
        return found

    def error_census(self) -> str:
        showing = [
            f"{ref.a1()}={cell.computed.code}"
            for ref, cell in self.engine.sheet.formula_cells()
            if is_error(cell.computed)
        ]
        if not showing:
            return "no cell currently shows an error"
        return (
            f"{len(showing)} cell(s) showing errors "
            f"({', '.join(showing)}); scrolled past is not "
            "resolved"
        )
