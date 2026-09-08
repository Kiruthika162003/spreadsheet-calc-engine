"""Spelling numbers: the check-writing function, exact about the cents.

Writing a number in words is the one place a spreadsheet
touches a legal instrument, a check, and the rules there are
not stylistic: the cents are written as a fraction over one
hundred, not as words, because "and fifty cents" invites the
alteration that "and 50/100" resists, and the word "and"
appears exactly once, separating dollars from cents, never
between hundreds and tens, because a check reading "one
hundred and five" has been the subject of actual litigation
over whether it means 105 or 100.05. Negative amounts are
refused rather than spelled, since a negative check is not a
document that exists and spelling one would be inventing a
financial instrument. The scale words run through trillions,
which is past any honest check and exactly the point: the
function refuses to spell what it cannot name rather than
falling back to digits halfway through, because a check that
switches from words to numerals mid-amount is a forgery
waiting to be alleged. Rounding to cents happens once, up
front, through Python's round, and the docstring's first
draft guessed that behavior wrong: it claimed 1.005 becomes
one cent, but 1.005 has no exact float and lands just below
the half, so it rounds to zero cents, while 2.675 lands just
above its half and rounds up to sixty-eight. The lesson kept
here is that decimal-looking rounding on binary floats is
not the clean half-to-even story it appears to be, and the
tests assert the measured cents rather than the imagined
ones.
"""

from __future__ import annotations

from gridiron.errors import Invalid

_ONES = (
    "zero", "one", "two", "three", "four", "five", "six",
    "seven", "eight", "nine", "ten", "eleven", "twelve",
    "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen",
)
_TENS = (
    "", "", "twenty", "thirty", "forty", "fifty", "sixty",
    "seventy", "eighty", "ninety",
)
_SCALES = (
    (10**12, "trillion"),
    (10**9, "billion"),
    (10**6, "million"),
    (10**3, "thousand"),
)


def _under_thousand(number: int) -> str:
    parts = []
    if number >= 100:
        parts.append(f"{_ONES[number // 100]} hundred")
        number %= 100
    if number >= 20:
        word = _TENS[number // 10]
        if number % 10:
            word += f"-{_ONES[number % 10]}"
        parts.append(word)
    elif number > 0:
        parts.append(_ONES[number])
    return " ".join(parts)


def spell_integer(number: int) -> str:
    if number < 0:
        raise Invalid(
            "a negative amount is not a check that exists"
        )
    if number == 0:
        return "zero"
    if number >= 10**15:
        raise Invalid(
            "the amount exceeds what this function will "
            "name; it refuses to switch to digits mid-word"
        )
    parts = []
    for value, name in _SCALES:
        if number >= value:
            parts.append(
                f"{_under_thousand(number // value)} {name}"
            )
            number %= value
    if number > 0:
        parts.append(_under_thousand(number))
    return " ".join(parts)


def _round_cents(amount: float) -> tuple[int, int]:
    total_cents = round(amount * 100)
    return divmod(total_cents, 100)


def spell_money(amount: float) -> str:
    if amount < 0:
        raise Invalid(
            "a negative check is not a document that exists"
        )
    dollars, cents = _round_cents(amount)
    dollar_word = spell_integer(dollars)
    unit = "dollar" if dollars == 1 else "dollars"
    return (
        f"{dollar_word} {unit} and {cents:02d}/100"
    )


def spell_number(amount: float) -> str:
    """Words for the whole part, refusing a fraction it would have to drop."""
    if amount != int(amount):
        raise Invalid(
            "spell_number takes whole numbers; use "
            "spell_money for amounts with cents"
        )
    return spell_integer(int(amount))
