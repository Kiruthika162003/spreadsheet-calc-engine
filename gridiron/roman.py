"""Roman numerals: the subtractive form, and the range it honestly covers.

Converting to and from Roman numerals is a small classic with
two traps worth stating. The first is subtractive notation:
four is IV, not IIII, and nine is IX, so the conversion must
emit the subtractive pairs rather than the additive runs a
naive greedy loop produces, which it does by including the
subtractive values in the greedy table itself. The second is
range: classic Roman numerals have no zero and no negative,
and the largest the standard form expresses without bars over
the letters is 3999, so the converter refuses anything
outside one to 3999 by name rather than emitting a string of
a thousand Ms that no one can read and nothing can parse
back. Parsing the other direction is strict: it accepts the
canonical form and rejects malformed strings like IIII or IC
rather than guessing their intent, because a lenient Roman
parser that accepts IIII must decide whether IIIII is five,
and down that road every string means something and nothing
means what it says. The round trip is the law the tests hold
to, every number from one to 3999 converts to a numeral and
back to itself, because a numeral system you cannot reverse
is decoration, not arithmetic.
"""

from __future__ import annotations

from gridiron.errors import Invalid

_TABLE = (
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
)


def to_roman(number: int) -> str:
    if not 1 <= number <= 3999:
        raise Invalid(
            f"{number} is outside 1 to 3999; classic Roman "
            "numerals have no zero, no negative, and no "
            "unbarred form past 3999"
        )
    result = []
    remaining = number
    for value, symbol in _TABLE:
        while remaining >= value:
            result.append(symbol)
            remaining -= value
    return "".join(result)


def from_roman(text: str) -> int:
    body = text.strip().upper()
    if not body:
        raise Invalid("an empty string is not a numeral")
    total = 0
    remaining = body
    for value, symbol in _TABLE:
        while remaining.startswith(symbol):
            total += value
            remaining = remaining[len(symbol) :]
    if remaining:
        raise Invalid(
            f"{text!r} is not a canonical Roman numeral; a "
            "lenient parser that accepts IIII must decide "
            "whether IIIII is five"
        )
    # Re-encode and compare: the only accepted spelling is
    # the canonical one, so IIII (which parses to 4 above
    # only if it reached here) is caught by disagreement.
    if to_roman(total) != body:
        raise Invalid(
            f"{text!r} is not the canonical spelling of "
            f"{total}, which is {to_roman(total)}"
        )
    return total
