"""The error doctor: every wound has a birthplace, and echoes are not patients.

Errors flow, which is the value model's virtue and the
debugger's curse: a #DIV/0! born in one denominator paints
twenty downstream cells, and the user staring at the last
one is nineteen cells from the problem. The doctor walks the
flow backward: a cell holding an error is an echo if any of
its precedent cells carries the same code, and the origin is
the cell at the end of that walk, the one whose precedents
are clean, because that is where the arithmetic actually
went wrong. The census leans on the same distinction, one
born and nineteen echoes is one bug, twenty born is twenty
bugs, and a census that reports twenty either way sends the
user on the wrong hunt. Each error code carries a
prescription, written as advice about the formula rather
than the symptom, guard the denominator, check the name's
spelling, chase the deleted geography, and the doctor
refuses to prescribe for codes it does not know rather than
dispensing generic comfort. Diagnosis of a healthy cell says
healthy, plainly, because a doctor who cannot say you are
fine is not trusted when it says you are not.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.values import ErrorValue, is_error

PRESCRIPTIONS = {
    "#DIV/0!": (
        "guard the denominator: IF(divisor=0, fallback, "
        "quotient) or vet the input that feeds it"
    ),
    "#VALUE!": (
        "a text or a bare range sat where a number was "
        "expected; coerce deliberately or fix the operand"
    ),
    "#REF!": (
        "the formula points at deleted geography; rewrite "
        "the reference, the sheet cannot guess where the "
        "old cell went"
    ),
    "#NAME?": (
        "define the name, register the table, or check the "
        "spelling; the engine refuses to guess at functions"
    ),
    "#CYCLE!": (
        "the formula sits on a reference loop; break the "
        "loop or move the calculation to the iterative "
        "solver on purpose"
    ),
    "#NUM!": (
        "the mathematics left the representable world or "
        "the question does not parse; check ranges, ranks, "
        "and sign conventions"
    ),
    "#N/A": (
        "the lookup found nothing; verify the key exists "
        "or wrap with IFERROR to state the fallback"
    ),
}


@dataclass(frozen=True)
class Diagnosis:
    ref: CellRef
    code: str
    origin: CellRef
    path: tuple[str, ...]

    def line(self) -> str:
        born_here = self.origin.key() == self.ref.key()
        if born_here:
            return (
                f"{self.ref.a1()}: {self.code} born here; "
                f"{PRESCRIPTIONS[self.code]}"
            )
        trail = " <- ".join(self.path)
        return (
            f"{self.ref.a1()}: {self.code} echoes from "
            f"{self.origin.a1()} ({trail}); "
            f"{PRESCRIPTIONS[self.code]}"
        )


@dataclass
class ErrorDoctor:
    engine: Engine

    def _error_at(self, ref: CellRef) -> ErrorValue | None:
        value = self.engine.value(ref)
        return value if is_error(value) else None

    def _precedent_cells(
        self, ref: CellRef
    ) -> list[CellRef]:
        cell = self.engine.sheet.cell(ref)
        if cell is None or cell.tree is None:
            return []
        found: list[CellRef] = []
        for precedent in cell.tree.refs():
            if isinstance(precedent, CellRef):
                found.append(precedent)
            else:
                found.extend(precedent.cells())
        return found

    def _walk_to_origin(
        self, ref: CellRef, code: str
    ) -> tuple[CellRef, list[str]]:
        current = ref
        path = [ref.a1()]
        visited = {ref.key()}
        while True:
            upstream = None
            for precedent in self._precedent_cells(current):
                if precedent.key() in visited:
                    continue
                wound = self._error_at(precedent)
                if wound is not None and wound.code == code:
                    upstream = precedent
                    break
            if upstream is None:
                return current, path
            visited.add(upstream.key())
            path.append(upstream.a1())
            current = upstream

    def diagnose(self, ref: CellRef) -> Diagnosis | str:
        wound = self._error_at(ref)
        if wound is None:
            return f"{ref.a1()} is healthy"
        if wound.code not in PRESCRIPTIONS:
            raise Invalid(
                f"no prescription for {wound.code}; the "
                "doctor does not dispense generic comfort"
            )
        origin, path = self._walk_to_origin(
            ref, wound.code
        )
        return Diagnosis(
            ref=ref,
            code=wound.code,
            origin=origin,
            path=tuple(path),
        )

    def census(self) -> str:
        born: dict[str, int] = {}
        echoes: dict[str, int] = {}
        for ref, _cell in self.engine.sheet.formula_cells():
            wound = self._error_at(ref)
            if wound is None:
                continue
            origin, _ = self._walk_to_origin(
                ref, wound.code
            )
            bucket = (
                born
                if origin.key() == ref.key()
                else echoes
            )
            bucket[wound.code] = (
                bucket.get(wound.code, 0) + 1
            )
        if not born and not echoes:
            return "no errors on the sheet"
        lines = []
        for code in sorted(set(born) | set(echoes)):
            lines.append(
                f"{code}: {born.get(code, 0)} born, "
                f"{echoes.get(code, 0)} echo(es)"
            )
        bugs = sum(born.values())
        lines.append(
            f"{bugs} distinct problem(s) to hunt"
        )
        return "\n".join(lines)
