"""Text layout: wrapping to a width and aligning within one, without losing a word.

Fitting text into a fixed-width cell or a report column is
word wrapping, and the rule that keeps it honest is that a
word is never split across lines unless it is itself longer
than the width, because a wrapped sentence with a word
guillotined in the middle is harder to read than one that
runs a hair long. A word longer than the width, a URL or a
part number, is placed on its own line whole rather than
broken, and the caller who needs hard breaking can ask for it
explicitly, because silent mid-word breaking of an
identifier corrupts it. Wrapping collapses runs of spaces
between words to single separators, the normalization every
wrapper performs, but it preserves the words themselves
exactly. Aligning pads a string to a width: left, right, or
centered, and centering that cannot split the odd space puts
the extra one on the right, the convention that keeps a
column of centered labels from jittering left and right by a
character. A string already at or over the width is returned
unchanged rather than truncated, because alignment adds
space and never removes content, and a caller who wants
truncation is asking a different function. The width must be
positive, since a column zero characters wide holds nothing
and wrapping into it would loop forever.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def wrap_text(text: str, width: int) -> list[str]:
    if width < 1:
        raise Invalid(
            "a column zero characters wide holds nothing"
        )
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def pad_left(text: str, width: int) -> str:
    if len(text) >= width:
        return text
    return " " * (width - len(text)) + text


def pad_right(text: str, width: int) -> str:
    if len(text) >= width:
        return text
    return text + " " * (width - len(text))


def center(text: str, width: int) -> str:
    if len(text) >= width:
        return text
    total = width - len(text)
    left = total // 2
    right = total - left
    return " " * left + text + " " * right
