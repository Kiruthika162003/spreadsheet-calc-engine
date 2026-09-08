"""The sheet: sparse storage where a cell is literal, formula, or absent.

A million-row sheet with forty entries stores forty entries;
absence is the dominant state and the storage respects it.
Each occupied cell is either a literal value or a formula,
and a formula cell keeps three things: the text as typed,
the tree as parsed once at entry, and the last computed
value, because parsing per recalc would tax every dependent
edit with every ancestor's grammar, and the text must
survive verbatim since the formula bar shows what the author
wrote, not a normalization of it. Setting a cell returns
what was displaced, so the undo stack upstream can be built
from returns instead of from spying on the storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.ast import Node
from gridiron.errors import Invalid
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.values import Value


@dataclass
class Cell:
    literal: Value = None
    formula_text: str | None = None
    tree: Node | None = None
    computed: Value = None

    def is_formula(self) -> bool:
        return self.formula_text is not None

    def current_value(self) -> Value:
        if self.is_formula():
            return self.computed
        return self.literal


@dataclass
class Sheet:
    cells: dict[tuple[int, int], Cell] = field(
        default_factory=dict
    )

    def set_literal(
        self, ref: CellRef, value: Value
    ) -> Cell | None:
        if isinstance(value, str) and value.startswith("="):
            raise Invalid(
                f"{ref.a1()}: text starting with = is a "
                "formula; route it through set_formula so the "
                "distinction stays deliberate"
            )
        displaced = self.cells.get(ref.key())
        self.cells[ref.key()] = Cell(literal=value)
        return displaced

    def set_formula(
        self, ref: CellRef, text: str
    ) -> Cell | None:
        if not text.startswith("="):
            raise Invalid(
                f"{ref.a1()}: a formula starts with =; "
                f"{text!r} looks like a literal"
            )
        tree = parse_formula(text)
        displaced = self.cells.get(ref.key())
        self.cells[ref.key()] = Cell(
            formula_text=text, tree=tree
        )
        return displaced

    def clear(self, ref: CellRef) -> Cell | None:
        return self.cells.pop(ref.key(), None)

    def cell(self, ref: CellRef) -> Cell | None:
        return self.cells.get(ref.key())

    def value_of(self, ref: CellRef) -> Value:
        held = self.cells.get(ref.key())
        if held is None:
            return None
        return held.current_value()

    def formula_cells(self) -> list[tuple[CellRef, Cell]]:
        return [
            (CellRef(row=row, col=col), cell)
            for (row, col), cell in sorted(self.cells.items())
            if cell.is_formula()
        ]

    def census(self) -> str:
        formulas = sum(
            1
            for cell in self.cells.values()
            if cell.is_formula()
        )
        literals = len(self.cells) - formulas
        return (
            f"{len(self.cells)} occupied cell(s): {literals} "
            f"literal(s), {formulas} formula(s); absence is "
            "the dominant state and the storage respects it"
        )
