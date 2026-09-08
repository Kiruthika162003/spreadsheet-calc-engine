"""The scenario proof: inputs swap together, atomically, and formulas stay off limits.

A scenario is a saved set of input values applied all at
once, and the property worth pinning is atomicity: applying
a two-input scenario must swap both inputs and recalculate
from the combined state, never show the output that a
half-applied scenario, one input changed and the other not,
would momentarily produce. The drill captures a base and an
optimistic scenario over two input cells feeding one output,
applies the optimistic one, and confirms the output reflects
both new inputs together, not either alone. Then it captures
the base back and reapplies to confirm the round trip
returns the original output exactly, because a scenario
manager that could not restore the baseline would be a
one-way door. The second half pins the boundary the module
draws in its own words: a scenario refuses to capture or
overwrite a formula cell, because a scenario that rewrites
formulas is editing the model and the two deserve different
verbs, and the drill confirms the refusal fires rather than
silently turning a computed cell into a literal.
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef
from gridiron.scenarios import ScenarioManager


def run() -> Finding:
    engine = Engine()
    engine.set_literal(CellRef.parse("A1"), 100.0)
    engine.set_literal(CellRef.parse("A2"), 10.0)
    engine.set_formula(CellRef.parse("B1"), "=A1*A2")
    manager = ScenarioManager(engine=engine)
    inputs = (CellRef.parse("A1"), CellRef.parse("A2"))
    manager.capture("base", inputs)
    baseline_output = engine.value(CellRef.parse("B1"))

    engine.set_literal(CellRef.parse("A1"), 200.0)
    engine.set_literal(CellRef.parse("A2"), 15.0)
    manager.capture("optimistic", inputs)

    manager.apply("base")
    after_base = engine.value(CellRef.parse("B1"))
    manager.apply("optimistic")
    after_optimistic = engine.value(CellRef.parse("B1"))

    formula_refused = False
    try:
        manager.capture(
            "bad", (CellRef.parse("B1"),)
        )
    except Invalid:
        formula_refused = True

    numbers = {
        "baseline_output": baseline_output,
        "after_base_restore": after_base,
        "after_optimistic": after_optimistic,
        "both_inputs_swapped": after_optimistic == 3000.0,
        "round_trip_restores": after_base == 1000.0,
        "formula_capture_refused": formula_refused,
    }
    holds = (
        baseline_output == 1000.0
        and after_base == 1000.0
        and after_optimistic == 3000.0
        and formula_refused
    )
    return Finding(
        proof="scenarioproof",
        claim=(
            "applying the optimistic scenario swaps both "
            "inputs together for an output of 3000, "
            "restoring base returns exactly 1000, and "
            "capturing a formula cell is refused as editing "
            "the model"
        ),
        numbers=numbers,
        holds=holds,
    )
