"""The workbook: sheets with names, and cross-sheet reads through one door.

A workbook is a namespace of sheets, and the discipline is
in the door: cross-sheet reads go through the workbook's
resolver, Sheet2!A1 style, never through direct object
references between sheets, because the resolver is where
renames stay coherent and where a read from a deleted sheet
becomes a #REF! instead of a Python error climbing out of a
formula. Sheet names are case-preserved but case-folded for
lookup, renames rewrite nothing because formulas store the
target name through the resolver's indirection, and deleting
a sheet that others reference is allowed with the damage
reported, not forbidden, because forbidding it just teaches
users to empty the sheet first and delete the husk, same
loss, worse audit trail.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid, Missing
from gridiron.refs import CellRef
from gridiron.sheet import Sheet
from gridiron.values import ErrorValue, Value


@dataclass
class Workbook:
    sheets: dict[str, Sheet] = field(default_factory=dict)
    display_names: dict[str, str] = field(
        default_factory=dict
    )

    def add_sheet(self, name: str) -> Sheet:
        folded = name.casefold()
        if not name.strip():
            raise Invalid("a sheet needs a name")
        if "!" in name:
            raise Invalid(
                "sheet names cannot carry the ! that "
                "separates them from references"
            )
        if folded in self.sheets:
            raise Invalid(
                f"a sheet named {self.display_names[folded]} "
                "already exists; case differences do not make "
                "two sheets"
            )
        sheet = Sheet()
        self.sheets[folded] = sheet
        self.display_names[folded] = name
        return sheet

    def sheet(self, name: str) -> Sheet:
        folded = name.casefold()
        if folded not in self.sheets:
            raise Missing(f"no sheet named {name}")
        return self.sheets[folded]

    def rename(self, old: str, new: str) -> str:
        folded_old = old.casefold()
        if folded_old not in self.sheets:
            raise Missing(f"no sheet named {old}")
        folded_new = new.casefold()
        if folded_new != folded_old and (
            folded_new in self.sheets
        ):
            raise Invalid(f"{new} is already taken")
        sheet = self.sheets.pop(folded_old)
        self.display_names.pop(folded_old)
        self.sheets[folded_new] = sheet
        self.display_names[folded_new] = new
        return f"{old} is now {new}"

    def drop_sheet(self, name: str) -> str:
        folded = name.casefold()
        if folded not in self.sheets:
            raise Missing(f"no sheet named {name}")
        del self.sheets[folded]
        display = self.display_names.pop(folded)
        readers = self._readers_of(folded)
        if readers:
            return (
                f"{display} dropped; {len(readers)} formula(s) "
                "elsewhere will now read #REF!, reported "
                "rather than forbidden, because forbidding "
                "teaches users to empty the sheet and delete "
                "the husk"
            )
        return f"{display} dropped; nobody was reading it"

    def _readers_of(self, folded: str) -> list[str]:
        found = []
        for sheet_name, sheet in self.sheets.items():
            for ref, cell in sheet.formula_cells():
                if f"{folded}!" in (
                    cell.formula_text or ""
                ).casefold():
                    found.append(
                        f"{self.display_names[sheet_name]}!"
                        f"{ref.a1()}"
                    )
        return found

    def read(self, sheet_name: str, ref: CellRef) -> Value:
        folded = sheet_name.casefold()
        if folded not in self.sheets:
            return ErrorValue(
                code="#REF!",
                note=(
                    f"sheet {sheet_name} does not exist; a "
                    "read through the resolver wounds instead "
                    "of raising"
                ),
            )
        return self.sheets[folded].value_of(ref)

    def census(self) -> str:
        lines = [f"{len(self.sheets)} sheet(s):"]
        for folded in sorted(self.sheets):
            sheet = self.sheets[folded]
            lines.append(
                f"  {self.display_names[folded]}: "
                f"{len(sheet.cells)} cell(s)"
            )
        return "\n".join(lines)
