"""Locales: the comma wars, fought once, with the strings kept out of it.

Half the world writes 1.234,56 and the other half writes
1,234.56, and a grid that serves either must treat notation
as a skin over one internal truth: values are floats,
formulas are trees, and locale is a rendering and parsing
concern that never touches storage. Rendering groups
thousands and swaps the decimal mark. Parsing is strict the
way the lexer taught: thousands separators must sit in
proper groups of three counting from the decimal mark, so
1,23,456 is refused rather than guessed, because the string
that parses under both locales to different numbers is the
most dangerous string in finance and strictness shrinks that
set. Formula translation swaps the list separator and the
decimal mark in one pass that walks the text respecting
string literals, since a formula saying \"Hello, world\" must
keep its comma while the argument separator beside it
changes costume, and the translation round-trips exactly:
comma world to point world and back is the identity, a law
the tests enforce on formulas with strings, decimals, and
nested calls at once. The decimal swap fires only between
digits, because the dot in ORDERS.AMOUNT is a table name's
punctuation and not arithmetic, and a translator that turns
a name into an argument list has not translated anything.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Locale:
    name: str
    decimal: str
    thousands: str
    list_sep: str


POINT = Locale(
    name="point",
    decimal=".",
    thousands=",",
    list_sep=",",
)
COMMA = Locale(
    name="comma",
    decimal=",",
    thousands=".",
    list_sep=";",
)


def render_number(
    value: float, locale: Locale, decimals: int = 2
) -> str:
    if decimals < 0:
        raise Invalid("decimals cannot be negative")
    sign = "-" if value < 0 else ""
    quantity = abs(value)
    whole = int(quantity)
    fraction = round(quantity - whole, decimals)
    if fraction >= 1.0:
        whole += 1
        fraction = 0.0
    digits = str(whole)
    grouped = ""
    for index, digit in enumerate(reversed(digits)):
        if index and index % 3 == 0:
            grouped = locale.thousands + grouped
        grouped = digit + grouped
    if decimals == 0:
        return sign + grouped
    fraction_text = f"{fraction:.{decimals}f}"[2:]
    return sign + grouped + locale.decimal + fraction_text


def parse_number(text: str, locale: Locale) -> float:
    body = text.strip()
    if not body:
        raise Invalid("an empty string is not a number")
    sign = 1.0
    if body[0] in "+-":
        sign = -1.0 if body[0] == "-" else 1.0
        body = body[1:]
    if locale.decimal in body:
        whole_part, _, fraction_part = body.partition(
            locale.decimal
        )
        if locale.decimal in fraction_part:
            raise Invalid(
                f"{text!r} carries two decimal marks"
            )
    else:
        whole_part, fraction_part = body, ""
    if fraction_part and not fraction_part.isdigit():
        raise Invalid(
            f"{text!r} has a broken fraction part"
        )
    if locale.thousands in whole_part:
        groups = whole_part.split(locale.thousands)
        if not groups[0] or len(groups[0]) > 3:
            raise Invalid(
                f"{text!r} misplaces a thousands "
                "separator; groups count in threes from "
                "the decimal mark"
            )
        for group in groups[1:]:
            if len(group) != 3 or not group.isdigit():
                raise Invalid(
                    f"{text!r} misplaces a thousands "
                    "separator; groups count in threes "
                    "from the decimal mark"
                )
        whole_part = "".join(groups)
    if not whole_part.isdigit():
        raise Invalid(f"{text!r} is not a number")
    value = float(whole_part)
    if fraction_part:
        value += float(f"0.{fraction_part}")
    return sign * value


def translate_formula(
    text: str, source: Locale, target: Locale
) -> str:
    if source == target:
        return text
    out: list[str] = []
    in_string = False
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            out.append(char)
            if (
                in_string
                and index + 1 < len(text)
                and text[index + 1] == '"'
            ):
                out.append('"')
                index += 2
                continue
            in_string = not in_string
            index += 1
            continue
        if in_string:
            out.append(char)
            index += 1
            continue
        if char == source.list_sep:
            out.append(target.list_sep)
        elif char == source.decimal and (
            (index > 0 and text[index - 1].isdigit())
            or (
                index + 1 < len(text)
                and text[index + 1].isdigit()
            )
        ):
            out.append(target.decimal)
        else:
            out.append(char)
        index += 1
    if in_string:
        raise Invalid(
            "the formula ends inside a string literal; "
            "translation refuses to guess where it closes"
        )
    return "".join(out)
