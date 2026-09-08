"""Information functions: asking a value what it is, and the fine distinctions that matter.

The IS family already answers the broad questions; this
module adds the narrow ones, and the narrowness is the point.
ISERR is not ISERROR: ISERR is true for every error except
#N/A, because #N/A means a lookup found nothing, a routine
and expected condition, while the other errors mean the
arithmetic broke, and a spreadsheet that could not tell
missing-on-purpose from broken would flag every empty lookup
as a failure. ISNA is its complement, true only for #N/A.
ISEVEN and ISODD test the parity of the truncated integer and
refuse a value that is not a number, because the parity of a
word is not false, it is a question that does not parse. N
coerces to a number the way the grid does, a true becoming
one and text becoming zero, while T does the mirror, passing
text through and turning everything else into the empty
string, and the two exist because a formula sometimes needs
to force a value onto one side of the number-text line
deliberately rather than hope the operators do. NA returns
the #N/A error on purpose, the one function whose whole job
is to produce an error, because a model with a
known-missing input should say so loudly rather than sit on
a zero that sums into a wrong total. TYPE names the kind as a
number the incumbent's way, so a formula can branch on what
it received.
"""

from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


def _one(args, lookup, functions, names, label):
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!",
            note=f"{label} takes one argument",
        )
    return evaluate(args[0], lookup, functions, names)


def _iserr(args, lookup, functions, names) -> Value:
    value = _one(args, lookup, functions, names, "ISERR")
    if isinstance(value, ErrorValue) and value.code != "#N/A":
        return True
    if isinstance(value, ErrorValue):
        return False
    return False


def _isna(args, lookup, functions, names) -> Value:
    value = _one(args, lookup, functions, names, "ISNA")
    return (
        isinstance(value, ErrorValue)
        and value.code == "#N/A"
    )


def _isnontext(args, lookup, functions, names) -> Value:
    value = _one(
        args, lookup, functions, names, "ISNONTEXT"
    )
    return not isinstance(value, str)


def _parity(want_even: bool, label: str):
    def run(args, lookup, functions, names) -> Value:
        value = _one(args, lookup, functions, names, label)
        if is_error(value):
            return value
        number = to_number(value)
        if is_error(number):
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"{label} of a non-number does not "
                    "parse; parity is a property of integers"
                ),
            )
        is_even = int(number) % 2 == 0
        return is_even if want_even else not is_even

    return run


def _n(args, lookup, functions, names) -> Value:
    value = _one(args, lookup, functions, names, "N")
    if is_error(value):
        return value
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, float):
        return value
    return 0.0


def _t(args, lookup, functions, names) -> Value:
    value = _one(args, lookup, functions, names, "T")
    if is_error(value):
        return value
    return value if isinstance(value, str) else ""


def _na(args, lookup, functions, names) -> Value:
    if args:
        return ErrorValue(
            code="#VALUE!", note="NA takes no arguments"
        )
    return ErrorValue(
        code="#N/A",
        note="NA is a deliberate missing value, said loudly",
    )


def _type(args, lookup, functions, names) -> Value:
    value = _one(args, lookup, functions, names, "TYPE")
    if isinstance(value, ErrorValue):
        return 16.0
    if isinstance(value, bool):
        return 4.0
    if isinstance(value, float):
        return 1.0
    if isinstance(value, str):
        return 2.0
    return 1.0


INFO_FUNCTIONS = {
    "ISERR": _iserr,
    "ISNA": _isna,
    "ISNONTEXT": _isnontext,
    "ISEVEN": _parity(True, "ISEVEN"),
    "ISODD": _parity(False, "ISODD"),
    "N": _n,
    "T": _t,
    "NA": _na,
    "TYPE": _type,
}
