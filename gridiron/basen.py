"""Arbitrary bases: writing a number in base two through thirty-six, and reading it back.

Beyond the fixed binary, octal, and hex of the engineering
module, the general BASE and DECIMAL pair writes a
non-negative integer in any base from two to thirty-six,
using the digits zero through nine then A through Z, the
convention every base-thirty-six identifier scheme assumes.
The base is bounded and the bound is stated: below two there
is no positional system, since base one is tally marks and
base zero is nothing, and above thirty-six the digits run out
of letters, so both ends are refused rather than producing
symbols no reader can decode. A minimum width is offered so a
column of codes aligns, padding with leading zeros, but it
never truncates a number that is already wider than the
minimum, because a code silently shortened is a different
code. Reading back is strict: every character must be a valid
digit for the base, so a Z in a base-sixteen string is
refused rather than skipped, because a dropped digit is a
wrong number that looks right, the same discipline the fixed-
base conversions hold. The round trip is a law the tests
enforce across every base, a number written and read back is
itself, because a positional system you cannot reverse is not
a numeral system. Negative numbers are refused, because these
bases have no sign convention and inventing one would
disagree with the two's-complement forms the engineering
module already committed to.
"""

from __future__ import annotations

from gridiron.errors import Invalid

_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def to_base(number: int, base: int, min_width: int = 0) -> str:
    if not 2 <= base <= 36:
        raise Invalid(
            f"base {base} is outside 2 to 36; below two "
            "there is no positional system and above "
            "thirty-six the digits run out of letters"
        )
    if number < 0:
        raise Invalid(
            "these bases have no sign convention; a negative "
            "would disagree with the two's-complement forms"
        )
    if number == 0:
        digits = "0"
    else:
        out = []
        remaining = number
        while remaining:
            out.append(_DIGITS[remaining % base])
            remaining //= base
        digits = "".join(reversed(out))
    return digits.rjust(min_width, "0")


def from_base(text: str, base: int) -> int:
    if not 2 <= base <= 36:
        raise Invalid(
            f"base {base} is outside 2 to 36"
        )
    body = text.strip().upper()
    if not body:
        raise Invalid("an empty string is not a number")
    value = 0
    for char in body:
        digit = _DIGITS.find(char)
        if digit < 0 or digit >= base:
            raise Invalid(
                f"{char!r} is not a base-{base} digit; a "
                "dropped digit is a wrong number that looks "
                "right"
            )
        value = value * base + digit
    return value
