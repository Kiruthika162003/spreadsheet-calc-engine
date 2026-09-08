"""The data-table proof: the sweep tabulates, and the world is put back exactly.

A what-if data table runs the model once per candidate and
its cardinal sin is leaving the sheet changed, so the drill
records the input cell's value before the sweep, runs a
one-variable sweep of several candidates, and confirms two
things: the tabulated outputs match the model evaluated at
each candidate, and the input cell afterward holds exactly
what it held before, because a what-if that leaves the world
changed is a what-now. The output cell after the sweep must
also read its original value, since restoring the input and
recalculating should return the whole model to where it
started. The two-variable form sweeps a grid and gets the
same restoration guarantee, checked by reading both input
cells back. The last probe pins the boundary the module
states: a sweep refuses to drive a formula cell as its
input, because sweeping the model instead of an input is the
mistake the discipline exists to prevent, and the refusal
fires rather than overwriting the formula with the first
candidate.
"""

from __future__ import annotations

from gridiron.datatable import DataTable
from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef


def run() -> Finding:
    engine = Engine()
    engine.set_literal(CellRef.parse("A1"), 5.0)
    engine.set_formula(CellRef.parse("B1"), "=A1*A1")
    table = DataTable(engine=engine)
    before = engine.value(CellRef.parse("A1"))
    output_before = engine.value(CellRef.parse("B1"))

    rows = table.one_variable(
        CellRef.parse("A1"),
        [1.0, 2.0, 3.0, 10.0],
        CellRef.parse("B1"),
    )
    swept = {float(c): v for c, v in rows}
    after = engine.value(CellRef.parse("A1"))
    output_after = engine.value(CellRef.parse("B1"))

    grid_engine = Engine()
    grid_engine.set_literal(CellRef.parse("A1"), 2.0)
    grid_engine.set_literal(CellRef.parse("A2"), 3.0)
    grid_engine.set_formula(
        CellRef.parse("B1"), "=A1+A2"
    )
    grid_table = DataTable(engine=grid_engine)
    grid_table.two_variable(
        CellRef.parse("A1"),
        [10.0, 20.0],
        CellRef.parse("A2"),
        [1.0, 2.0],
        CellRef.parse("B1"),
    )
    grid_restored = (
        grid_engine.value(CellRef.parse("A1")) == 2.0
        and grid_engine.value(CellRef.parse("A2")) == 3.0
    )

    formula_refused = False
    try:
        table.one_variable(
            CellRef.parse("B1"),
            [1.0],
            CellRef.parse("B1"),
        )
    except Invalid:
        formula_refused = True

    numbers = {
        "swept_values": swept,
        "outputs_match_model": (
            swept[3.0] == "9" and swept[10.0] == "100"
        ),
        "input_restored": after == before,
        "output_restored": output_after == output_before,
        "grid_restored": grid_restored,
        "formula_sweep_refused": formula_refused,
    }
    holds = (
        numbers["outputs_match_model"]
        and after == 5.0
        and output_after == 25.0
        and grid_restored
        and formula_refused
    )
    return Finding(
        proof="datatableproof",
        claim=(
            "a one-variable sweep tabulates 3 to 9 and 10 to "
            "100 then restores the input to 5 and the output "
            "to 25, the two-variable form restores both "
            "inputs, and sweeping a formula cell is refused"
        ),
        numbers=numbers,
        holds=holds,
    )
