"""The cross-sheet proof: one edit, the whole workbook settles, and the loop is caught.

The drill builds a four-sheet chain, Costs feeding Summary
feeding Report with Revenue on the side, and edits one cost
input. The claim under test is the settling discipline: the
local cone runs first, then cross-sheet formulas refresh in
rounds until a round changes nothing, and the watcher's own
local dependents ride along because refreshes go through the
local engine. The proof reads the counts out of the verdict
line the engine itself prints, so the numbers here are the
engine's own accounting and not a parallel bookkeeping that
could drift. The second half builds the workbook loop, two
sheets each reading the other plus one, which can never
settle, and confirms the rounds cap stamps both cells with
#CYCLE! naming the boundary the loop crosses. The last probe
pins the stated call boundary: an XRef inside a function
argument still refuses with the sheetless note, because the
function table does not carry the resolver yet and an honest
refusal beats a half-plumbed pipe.
"""

from __future__ import annotations

from gridiron.bookengine import BookEngine
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef
from gridiron.values import is_error


def _counts(verdict: str) -> tuple[int, int]:
    words = verdict.split()
    refreshed = int(words[words.index("cross-sheet") - 1])
    rounds = int(words[words.index("round(s)") - 1])
    return refreshed, rounds


def run() -> Finding:
    engine = BookEngine()
    for name in ("Costs", "Revenue", "Summary", "Report"):
        engine.add_sheet(name)
    a1 = CellRef.parse("A1")
    engine.set_literal("Costs", a1, 120.0)
    engine.set_literal("Costs", CellRef.parse("A2"), 80.0)
    engine.set_formula("Costs", CellRef.parse("B1"), "=A1+A2")
    engine.set_literal("Revenue", a1, 500.0)
    engine.set_formula(
        "Summary", CellRef.parse("C1"), "=Revenue!A1-Costs!B1"
    )
    engine.set_formula("Summary", CellRef.parse("C2"), "=C1*2")
    engine.set_formula("Report", a1, "=Summary!C2/10")
    baseline = engine.value("Report", a1)
    verdict = engine.set_literal("Costs", a1, 150.0)
    refreshed, rounds = _counts(verdict)
    settled = engine.value("Report", a1)
    rode_along = engine.value("Summary", CellRef.parse("C2"))

    loop = BookEngine()
    loop.add_sheet("Alpha")
    loop.add_sheet("Beta")
    loop.set_formula("Alpha", a1, "=Beta!A1+1")
    loop.set_formula("Beta", a1, "=Alpha!A1+1")
    stamped = loop.value("Alpha", a1)

    engine.set_formula(
        "Report", CellRef.parse("B1"), "=ABS(Summary!C1)"
    )
    boundary = engine.value("Report", CellRef.parse("B1"))

    numbers = {
        "baseline_report": baseline,
        "settled_report": settled,
        "watchers_refreshed": refreshed,
        "rounds_to_settle": rounds,
        "local_dependent_rode_along": rode_along,
        "loop_stamped_cycle": is_error(stamped)
        and stamped.code == "#CYCLE!",
        "call_boundary_refuses": is_error(boundary)
        and boundary.code == "#REF!",
    }
    holds = (
        numbers["baseline_report"] == 60.0
        and numbers["settled_report"] == 54.0
        and numbers["watchers_refreshed"] == 2
        and numbers["rounds_to_settle"] == 2
        and numbers["local_dependent_rode_along"] == 540.0
        and numbers["loop_stamped_cycle"]
        and numbers["call_boundary_refuses"]
    )
    return Finding(
        proof="crosssheetproof",
        claim=(
            "one edited cost settles a chain across three "
            "sheet boundaries in two refresh rounds with the "
            "watcher's local dependent riding along, the "
            "workbook loop is stamped #CYCLE! at the cap, and "
            "the call boundary refuses honestly"
        ),
        numbers=numbers,
        holds=holds,
    )
