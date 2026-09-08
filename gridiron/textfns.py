"""Text functions: one-based, like the users who type them.

Spreadsheet text functions are one-based and always have
been: MID("ledger", 1, 3) is "led", and an engine that
zero-indexed for the implementer's comfort would break every
formula pasted in from thirty years of workbooks. The
family here follows the incumbent's edge cases where they
are defensible, LEFT past the end returns the whole text
rather than erroring, LEN counts characters not bytes, and
refuses where they are not: a negative count is a #VALUE!
with the argument named, because silently clamping a
negative to zero hides the arithmetic bug that produced it.
Numbers flowing into text positions coerce through the
value module's narrow gate, so TRUE never becomes a length
and text never becomes a start position by accident.
"""

from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    render,
    to_number,
)


def _text_arg(args, index, lookup, functions, names) -> str | ErrorValue:
    value = evaluate(args[index], lookup, functions, names)
    if is_error(value):
        return value
    return render(value)


def _count_arg(
    args, index, lookup, functions, names
) -> int | ErrorValue:
    value = to_number(
        evaluate(args[index], lookup, functions, names)
    )
    if is_error(value):
        return value
    if value < 0:
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"argument {index + 1} is negative; clamping "
                "it would hide the arithmetic bug that "
                "produced it"
            ),
        )
    return int(value)


def _arity(args, *allowed: int) -> ErrorValue | None:
    if len(args) not in allowed:
        return ErrorValue(
            code="#VALUE!",
            note=f"expected {allowed} argument(s), got {len(args)}",
        )
    return None


def _left(args, lookup, functions, names) -> Value:
    bad = _arity(args, 1, 2)
    if bad:
        return bad
    text = _text_arg(args, 0, lookup, functions, names)
    if is_error(text):
        return text
    count = 1
    if len(args) == 2:
        count = _count_arg(args, 1, lookup, functions, names)
        if is_error(count):
            return count
    return text[:count]


def _right(args, lookup, functions, names) -> Value:
    bad = _arity(args, 1, 2)
    if bad:
        return bad
    text = _text_arg(args, 0, lookup, functions, names)
    if is_error(text):
        return text
    count = 1
    if len(args) == 2:
        count = _count_arg(args, 1, lookup, functions, names)
        if is_error(count):
            return count
    return text[-count:] if count else ""


def _mid(args, lookup, functions, names) -> Value:
    bad = _arity(args, 3)
    if bad:
        return bad
    text = _text_arg(args, 0, lookup, functions, names)
    if is_error(text):
        return text
    start = _count_arg(args, 1, lookup, functions, names)
    if is_error(start):
        return start
    if start == 0:
        return ErrorValue(
            code="#VALUE!",
            note="MID is one-based, like the users who type it",
        )
    count = _count_arg(args, 2, lookup, functions, names)
    if is_error(count):
        return count
    return text[start - 1 : start - 1 + count]


def _len(args, lookup, functions, names) -> Value:
    bad = _arity(args, 1)
    if bad:
        return bad
    text = _text_arg(args, 0, lookup, functions, names)
    if is_error(text):
        return text
    return float(len(text))


def _upper(args, lookup, functions, names) -> Value:
    bad = _arity(args, 1)
    if bad:
        return bad
    text = _text_arg(args, 0, lookup, functions, names)
    if is_error(text):
        return text
    return text.upper()


def _lower(args, lookup, functions, names) -> Value:
    bad = _arity(args, 1)
    if bad:
        return bad
    text = _text_arg(args, 0, lookup, functions, names)
    if is_error(text):
        return text
    return text.lower()


def _trim(args, lookup, functions, names) -> Value:
    bad = _arity(args, 1)
    if bad:
        return bad
    text = _text_arg(args, 0, lookup, functions, names)
    if is_error(text):
        return text
    return " ".join(text.split())


TEXT_FUNCTIONS = {
    "LEFT": _left,
    "RIGHT": _right,
    "MID": _mid,
    "LEN": _len,
    "UPPER": _upper,
    "LOWER": _lower,
    "TRIM": _trim,
}
