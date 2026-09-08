"""The volatile proof: no ambient clock, and the same seed replays exactly.

RAND and TODAY are where determinism dies in most engines,
because they reach for a global generator and the wall clock,
and a workbook that computes a different number every time it
opens is a workbook no one can test or audit. This package
refuses the ambient versions entirely, and the drill proves
it: evaluating RAND with only the standard function table,
no volatile context, returns #NAME? with a note that there
is no global generator anywhere, so a formula cannot secretly
depend on hidden state. With a context supplied, the drill
evaluates a sequence of RAND draws under one seed, then
rebuilds a fresh context with the same seed and draws again,
and confirms the two sequences are identical, because the
same seed must replay exactly or the determinism is a
decoration. TODAY returns the context's fixed serial rather
than a real date, so a sheet dated for a test stays dated
there. The last check is that two different seeds produce
different sequences, because a generator that ignored its
seed would be deterministic in the worst way, always the
same regardless of what the caller asked for.
"""

from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.proofs.finding import Finding
from gridiron.values import is_error
from gridiron.volatilefns import VolatileContext


def _draws(seed: int, count: int) -> list[float]:
    context = VolatileContext(seed=seed, today_serial=100)
    volatile = context.make_functions()

    def table(name: str):
        found = volatile.get(name)
        return found if found is not None else full_table(name)

    return [
        evaluate(parse_formula("=RAND()"), lambda _r: None, table)
        for _ in range(count)
    ]


def run() -> Finding:
    ambient = evaluate(
        parse_formula("=RAND()"),
        lambda _r: None,
        full_table,
    )
    ambient_refused = (
        is_error(ambient) and ambient.code == "#NAME?"
    )

    first = _draws(seed=42, count=5)
    again = _draws(seed=42, count=5)
    other = _draws(seed=99, count=5)

    context = VolatileContext(seed=1, today_serial=250)
    today = context.make_functions()["TODAY"]
    today_value = today((), lambda _r: None, full_table, None)

    numbers = {
        "ambient_refused": ambient_refused,
        "replays_exactly": first == again,
        "seed_changes_the_stream": first != other,
        "today_is_the_fixed_serial": today_value == 250.0,
        "draws_are_in_unit_interval": all(
            0.0 <= x < 1.0 for x in first
        ),
    }
    holds = (
        ambient_refused
        and first == again
        and first != other
        and today_value == 250.0
        and numbers["draws_are_in_unit_interval"]
    )
    return Finding(
        proof="volatileproof",
        claim=(
            "RAND without a context is #NAME? with no ambient "
            "generator, the same seed replays an identical "
            "sequence while a different seed diverges, and "
            "TODAY returns the context's fixed serial"
        ),
        numbers=numbers,
        holds=holds,
    )
