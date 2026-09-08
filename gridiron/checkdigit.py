"""Check digits: the arithmetic that catches a mistyped number before it costs.

A check digit is a small piece of redundancy that turns a
single-digit typo or an adjacent transposition into a
detectable error, and a spreadsheet validating account
numbers, cards, or ISBNs needs the exact algorithm, not a
plausible one, because a check that passes a bad number is
worse than no check at all. The Luhn algorithm, behind
payment cards, doubles every second digit from the right and
sums the digits of the doubled values, and the number is
valid when the total is a multiple of ten; the doubling
detail that trips reimplementations is that a doubled nine
becomes eighteen and contributes nine, not eighteen, so the
digit-sum is taken rather than the value. ISBN-10 weights its
digits ten down to one and validates modulo eleven, with the
final check position allowed to be the letter X standing for
ten, a real value the digit cannot hold, refused if it
appears anywhere but last. ISBN-13 is a Luhn cousin weighting
one and three alternately modulo ten. Each function reports
validity rather than raising, because an invalid number is a
data condition the caller expects and wants to branch on, not
an exception, but a string with non-digit characters where
digits belong is a different thing, a malformed input rather
than a failed check, and that is refused so a caller never
mistakes garbage for a clean rejection.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def _digits(text: str) -> list[int]:
    stripped = text.replace("-", "").replace(" ", "")
    if not stripped.isdigit():
        raise Invalid(
            f"{text!r} has non-digit characters where a "
            "number was expected; a malformed input is not "
            "a failed check"
        )
    return [int(c) for c in stripped]


def luhn_valid(text: str) -> bool:
    digits = _digits(text)
    if not digits:
        return False
    total = 0
    for index, digit in enumerate(reversed(digits)):
        if index % 2 == 1:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit
    return total % 10 == 0


def isbn10_valid(text: str) -> bool:
    body = text.replace("-", "").replace(" ", "").upper()
    if len(body) != 10:
        return False
    total = 0
    for index, char in enumerate(body):
        if char == "X":
            if index != 9:
                raise Invalid(
                    "X may stand for ten only in the final "
                    "ISBN-10 position"
                )
            value = 10
        elif char.isdigit():
            value = int(char)
        else:
            raise Invalid(
                f"{text!r} has a character that is neither a "
                "digit nor a final X"
            )
        total += value * (10 - index)
    return total % 11 == 0


def isbn13_valid(text: str) -> bool:
    digits = _digits(text)
    if len(digits) != 13:
        return False
    total = sum(
        digit * (1 if index % 2 == 0 else 3)
        for index, digit in enumerate(digits)
    )
    return total % 10 == 0


def luhn_check_digit(text: str) -> int:
    """The digit that would make `text` (a partial number) valid."""
    digits = _digits(text)
    total = 0
    for index, digit in enumerate(reversed(digits)):
        # The check digit will sit at position 0, so the
        # existing digits shift up by one in the doubling
        # parity.
        if index % 2 == 0:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit
    return (10 - total % 10) % 10
