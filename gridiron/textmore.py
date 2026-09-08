"""Text splitting: cut at a delimiter, and be precise about what happens at the edges.

The modern text functions are about slicing a string at a
delimiter, and every one of them hides an edge case that
separates a careful implementation from a frustrating one.
TEXTBEFORE returns what precedes the first occurrence of a
delimiter, TEXTAFTER what follows it, and the question both
must answer honestly is what to do when the delimiter is
absent: this family returns #N/A rather than the whole string
or an empty one, because silently handing back the entire
string when the split failed is how a parser downstream
treats an unsplit line as a valid single field and never
notices. An instance number selects which occurrence to cut
at, negative counting from the end, so TEXTAFTER of a path at
instance minus one is the filename after the last slash, the
operation everyone actually wants. TEXTSPLIT breaks a string
into all its pieces at a delimiter, and an empty delimiter is
refused rather than splitting into individual characters,
because splitting on nothing is a different function wearing
this one's name; because it yields a list rather than a
scalar, it is a module helper for the array world instead of
a cell function, held to the same empty-delimiter refusal.
CONCAT joins values with no separator, rendering numbers the
way the grid renders them. CLEAN strips the control
characters that arrive from copy-paste and break exports.
"""

from __future__ import annotations

from gridiron.ast import Range
from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    render,
    to_number,
)


def _text(arg, lookup, functions, names) -> Value:
    value = evaluate(arg, lookup, functions, names)
    if is_error(value):
        return value
    if value is None:
        return ""
    return value if isinstance(value, str) else render(value)


def _number(arg, lookup, functions, names) -> Value:
    value = evaluate(arg, lookup, functions, names)
    if is_error(value):
        return value
    return to_number(value)


def _cut(before: bool):
    def run(args, lookup, functions, names) -> Value:
        if len(args) not in (2, 3):
            label = (
                "TEXTBEFORE" if before else "TEXTAFTER"
            )
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"{label} takes text, a delimiter, and "
                    "an optional instance"
                ),
            )
        text = _text(args[0], lookup, functions, names)
        if is_error(text):
            return text
        delimiter = _text(
            args[1], lookup, functions, names
        )
        if is_error(delimiter):
            return delimiter
        if delimiter == "":
            return ErrorValue(
                code="#VALUE!",
                note="an empty delimiter cuts nowhere",
            )
        instance = 1
        if len(args) == 3:
            n = _number(
                args[2], lookup, functions, names
            )
            if is_error(n):
                return n
            instance = int(n)
        positions = _occurrences(text, delimiter)
        if not positions:
            return ErrorValue(
                code="#N/A",
                note=(
                    f"the delimiter {delimiter!r} is not in "
                    "the text; returning the whole string "
                    "would hide the failed split"
                ),
            )
        if instance < 0:
            index = len(positions) + instance
        else:
            index = instance - 1
        if not 0 <= index < len(positions):
            return ErrorValue(
                code="#N/A",
                note=(
                    f"instance {instance} is beyond the "
                    f"{len(positions)} occurrence(s)"
                ),
            )
        cut = positions[index]
        if before:
            return text[:cut]
        return text[cut + len(delimiter) :]

    return run


def _occurrences(text: str, delimiter: str) -> list[int]:
    positions = []
    start = 0
    while True:
        found = text.find(delimiter, start)
        if found == -1:
            break
        positions.append(found)
        start = found + len(delimiter)
    return positions


def text_split(text: str, delimiter: str) -> list[str]:
    if delimiter == "":
        raise Invalid(
            "splitting on an empty delimiter is a different "
            "function; this one cuts at a delimiter"
        )
    return text.split(delimiter)


def _concat(args, lookup, functions, names) -> Value:
    pieces: list[str] = []
    for arg in args:
        if isinstance(arg, Range):
            for cell in arg.ref.cells():
                value = lookup(cell)
                if is_error(value):
                    return value
                if value is not None:
                    pieces.append(
                        value
                        if isinstance(value, str)
                        else render(value)
                    )
        else:
            text = _text(arg, lookup, functions, names)
            if is_error(text):
                return text
            pieces.append(text)
    return "".join(pieces)


def _clean(args, lookup, functions, names) -> Value:
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!", note="CLEAN takes one text"
        )
    text = _text(args[0], lookup, functions, names)
    if is_error(text):
        return text
    return "".join(c for c in text if ord(c) >= 32)


TEXT_MORE_FUNCTIONS = {
    "TEXTBEFORE": _cut(before=True),
    "TEXTAFTER": _cut(before=False),
    "CONCAT": _concat,
    "CLEAN": _clean,
}
