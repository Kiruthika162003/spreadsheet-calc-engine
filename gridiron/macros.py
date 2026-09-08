"""Macros: a recorded sequence of edits, replayable and relocatable.

A macro here is not a scripting language, which is a
different and larger thing; it is the honest small version,
a recorded list of edits that can be replayed on demand. The
recording captures intent, set this cell to this literal, set
that cell to this formula, clear this one, rather than
capturing the resulting values, because a macro that recorded
computed values would replay a photograph instead of an
action and break the moment its inputs differ. Replay is
transactional in spirit: the steps run in order against a
target engine, and because each step is a described intent
rather than a closure over the original sheet, a macro
recorded on one sheet replays on another. Relocation is the
useful trick, replaying a macro shifted by a row and column
offset so a procedure recorded once at A1 can be applied at
D10, and the shift reuses the paste module's reference
rewriter so formulas relocate correctly rather than by naive
text surgery. A shift that would push a cell off the top or
left edge is refused before any step runs, because a macro
that half-applies has left the sheet in a state no one
intended and no undo entry describes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.paste import shifted_formula
from gridiron.refs import CellRef
from gridiron.values import Value


@dataclass(frozen=True)
class Step:
    kind: str
    ref: CellRef
    payload: object = None


@dataclass
class MacroRecorder:
    steps: list[Step] = field(default_factory=list)

    def record_literal(
        self, ref: CellRef, value: Value
    ) -> None:
        self.steps.append(
            Step(kind="literal", ref=ref, payload=value)
        )

    def record_formula(
        self, ref: CellRef, text: str
    ) -> None:
        self.steps.append(
            Step(kind="formula", ref=ref, payload=text)
        )

    def record_clear(self, ref: CellRef) -> None:
        self.steps.append(Step(kind="clear", ref=ref))

    def _shifted_ref(
        self, ref: CellRef, rows: int, cols: int
    ) -> CellRef:
        try:
            return ref.shifted(rows, cols)
        except Invalid as refusal:
            raise Invalid(
                f"replaying at offset ({rows}, {cols}) "
                f"pushes {ref.a1()} off the sheet; a macro "
                "that half-applies leaves a state no one "
                "intended"
            ) from refusal

    def replay(
        self,
        engine: Engine,
        rows: int = 0,
        cols: int = 0,
    ) -> str:
        planned = []
        for step in self.steps:
            target = self._shifted_ref(step.ref, rows, cols)
            planned.append((step, target))
        applied = 0
        for step, target in planned:
            if step.kind == "literal":
                engine.set_literal(target, step.payload)
            elif step.kind == "formula":
                text = step.payload
                if rows or cols:
                    text = shifted_formula(
                        text, rows, cols
                    )
                engine.set_formula(target, text)
            elif engine.sheet.cell(target) is not None:
                engine.clear(target)
            applied += 1
        where = (
            f" at offset ({rows}, {cols})"
            if rows or cols
            else ""
        )
        return f"replayed {applied} step(s){where}"

    def describe(self) -> str:
        lines = []
        for step in self.steps:
            if step.kind == "literal":
                lines.append(
                    f"{step.ref.a1()} = {step.payload!r}"
                )
            elif step.kind == "formula":
                lines.append(
                    f"{step.ref.a1()}: {step.payload}"
                )
            else:
                lines.append(f"clear {step.ref.a1()}")
        return "\n".join(lines)
