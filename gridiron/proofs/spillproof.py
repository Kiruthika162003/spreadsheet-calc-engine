"""The spill proof: all or nothing, ghosts counted, the blocker named.

The drill lands a transposed grid, counts its ghosts, and
checks the two corruption guards the spill module promises.
First the blocked landing: a value planted where the next
spill wants to land must stop the whole rectangle, leaving
the anchor holding #SPILL! with the blocker's address in the
note and zero new ghosts registered, because a half-landed
spill is corruption arranged in a rectangle and a partial
ghost registry is the bookkeeping of that corruption. Then
the sweep: clearing the anchor must remove every ghost it
owns and no cell it does not, measured by reading a bystander
cell after the sweep. The ghost census is the number worth
watching here: a two-by-three grid owns five ghosts, the
anchor being the sixth cell and its own landlord, and the
guard on editing a ghost names the anchor so the user fixes
the formula instead of fighting its shadow.
"""

from __future__ import annotations

from gridiron.arrays import ArrayLab
from gridiron.errors import Invalid
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.spill import SpillManager
from gridiron.values import is_error


def run() -> Finding:
    sheet = Sheet()
    for address, value in (
        ("A1", 1.0),
        ("B1", 2.0),
        ("C1", 3.0),
        ("A2", 4.0),
        ("B2", 5.0),
        ("C2", 6.0),
    ):
        sheet.set_literal(CellRef.parse(address), value)
    lab = ArrayLab(
        sheet=sheet, spill=SpillManager(sheet=sheet)
    )
    verdict = lab.transpose_region(
        RangeRef.parse("A1:C2"), CellRef.parse("E1")
    )
    ghost_census = len(
        lab.spill.anchors[CellRef.parse("E1").key()]
    )
    guard_names_anchor = False
    try:
        lab.spill.edit_guard(CellRef.parse("F3"))
    except Invalid as refusal:
        guard_names_anchor = "E1" in str(refusal)

    sheet.set_literal(CellRef.parse("H2"), 99.0)
    blocked = lab.transpose_region(
        RangeRef.parse("A1:C2"), CellRef.parse("H1")
    )
    blocked_cleanly = (
        is_error(blocked)
        and "blocked by H2" in blocked.note
        and CellRef.parse("H1").key()
        not in lab.spill.anchors
    )

    sweep = lab.spill.clear_anchor(CellRef.parse("E1"))
    bystander = sheet.value_of(CellRef.parse("H2"))
    swept_clean = (
        "5 ghost(s) swept" in sweep
        and sheet.value_of(CellRef.parse("F3")) is None
        and bystander == 99.0
    )

    numbers = {
        "landing_verdict": verdict,
        "ghost_census": ghost_census,
        "guard_names_anchor": guard_names_anchor,
        "blocked_all_or_nothing": blocked_cleanly,
        "swept_clean_with_bystander": swept_clean,
    }
    holds = (
        verdict == "3x2 grid spilled from E1"
        and ghost_census == 5
        and guard_names_anchor
        and blocked_cleanly
        and swept_clean
    )
    return Finding(
        proof="spillproof",
        claim=(
            "a three-by-two landing owns five ghosts, the "
            "blocked rectangle refuses whole with the "
            "blocker named and no ghosts registered, and "
            "the sweep clears every ghost while the "
            "bystander survives"
        ),
        numbers=numbers,
        holds=holds,
    )
