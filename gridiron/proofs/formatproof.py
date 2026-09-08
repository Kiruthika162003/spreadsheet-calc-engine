"""The format proof: the display rounds, the value does not, and the total knows.

The one property worth a dedicated drill is the separation
of display from storage, because it is the source of half of
all spreadsheet support tickets, the totals do not match
what I see. The drill puts 2.4 and 2.4 in two cells formatted
to zero decimals, so each displays as 2, and sums them: the
displayed digits invite the reader to expect 2 plus 2 equals
4, but the stored values sum to 4.8 and the total cell,
formatted the same way, displays 5. That gap, 2 and 2 making
5, is not a bug; it is the proof that formatting never
touched the numbers, and a renderer that rounded storage
would have made the comfortable, wrong 4. The second half
confirms the format language's working core in one pass:
grouping, percent, and a negative section in parentheses,
each read off the same value model, and an unknown code
refused at parse time rather than rendering a guess.
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.numberformat import NumberFormat
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef


def run() -> Finding:
    engine = Engine()
    engine.set_literal(CellRef.parse("A1"), 2.4)
    engine.set_literal(CellRef.parse("A2"), 2.4)
    engine.set_formula(CellRef.parse("A3"), "=A1+A2")
    whole = NumberFormat.parse("0")
    shown_a1 = whole.apply(engine.value(CellRef.parse("A1")))
    shown_a2 = whole.apply(engine.value(CellRef.parse("A2")))
    stored_total = engine.value(CellRef.parse("A3"))
    shown_total = whole.apply(stored_total)

    grouped = NumberFormat.parse("#,##0").apply(1234567.0)
    percent = NumberFormat.parse("0%").apply(0.1234)
    negative = NumberFormat.parse("0.00;(0.00)").apply(-3.5)

    unknown_refused = False
    try:
        NumberFormat.parse("q?z")
    except Invalid:
        unknown_refused = True

    numbers = {
        "shown_a1": shown_a1,
        "shown_a2": shown_a2,
        "stored_total": stored_total,
        "shown_total": shown_total,
        "display_lies_storage_does_not": (
            shown_a1 == "2"
            and shown_a2 == "2"
            and stored_total == 4.8
            and shown_total == "5"
        ),
        "grouped": grouped,
        "percent": percent,
        "negative_parenthesized": negative,
        "unknown_code_refused": unknown_refused,
    }
    holds = (
        numbers["display_lies_storage_does_not"]
        and grouped == "1,234,567"
        and percent == "12%"
        and negative == "(3.50)"
        and unknown_refused
    )
    return Finding(
        proof="formatproof",
        claim=(
            "two cells shown as 2 store 2.4 each and total "
            "to a cell shown as 5, proving format never "
            "touches storage, while grouping, percent, and "
            "the negative section render off the same value"
        ),
        numbers=numbers,
        holds=holds,
    )
