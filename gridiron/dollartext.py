"""DOLLAR and FIXED: numbers rendered as text, with the grouping and the sign.

These two turn a number into a formatted string, and unlike a
number format, which is a display skin over a value that stays
a number, these produce actual text a formula can then
concatenate into a sentence. DOLLAR prepends a currency sign
and groups thousands; FIXED does the same grouping without the
sign and can suppress the grouping when asked, for the cases
where a formatted number feeds a system that chokes on commas.
Both round to the requested number of decimals through the
same round the rest of the engine uses, so DOLLAR of a value
agrees to the penny with what ROUND would give, and a
negative number wears its minus sign outside the currency
symbol, minus dollar one, not dollar minus one, because the
sign belongs to the quantity and burying it inside the symbol
is how a refund reads as a charge. A negative decimal count
rounds to the left of the decimal point, so FIXED of 1234 at
minus two is 1200, the incumbent's behavior and genuinely
useful for order-of-magnitude tables, refused only when it
would round away the entire number into nothing. The result
is always text, even for a whole number, because the whole
point is to leave the numeric world and enter the string
one deliberately.
"""

from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


def _grouped(whole: str, use_commas: bool) -> str:
    if not use_commas:
        return whole
    digits = whole.lstrip("-")
    sign = "-" if whole.startswith("-") else ""
    grouped = ""
    for index, digit in enumerate(reversed(digits)):
        if index and index % 3 == 0:
            grouped = "," + grouped
        grouped = digit + grouped
    return sign + grouped


def _format(
    number: float, decimals: int, use_commas: bool
) -> str:
    if decimals >= 0:
        rounded = round(number, decimals)
        text = f"{abs(rounded):.{decimals}f}"
        if "." in text:
            whole, frac = text.split(".")
        else:
            whole, frac = text, ""
        grouped = _grouped(whole, use_commas)
        sign = "-" if rounded < 0 else ""
        return (
            f"{sign}{grouped}.{frac}"
            if frac
            else f"{sign}{grouped}"
        )
    factor = 10 ** (-decimals)
    rounded = round(number / factor) * factor
    text = str(abs(int(rounded)))
    grouped = _grouped(text, use_commas)
    sign = "-" if rounded < 0 else ""
    return f"{sign}{grouped}"


def _decimals_arg(args, index, lookup, functions, names):
    if len(args) <= index:
        return 2
    value = to_number(
        evaluate(args[index], lookup, functions, names)
    )
    if is_error(value):
        return value
    return int(value)


def _dollar(args, lookup, functions, names) -> Value:
    if not 1 <= len(args) <= 2:
        return ErrorValue(
            code="#VALUE!",
            note="DOLLAR takes a number and optional decimals",
        )
    number = to_number(
        evaluate(args[0], lookup, functions, names)
    )
    if is_error(number):
        return number
    decimals = _decimals_arg(
        args, 1, lookup, functions, names
    )
    if is_error(decimals):
        return decimals
    body = _format(number, decimals, use_commas=True)
    if body.startswith("-"):
        return f"-${body[1:]}"
    return f"${body}"


def _fixed(args, lookup, functions, names) -> Value:
    if not 1 <= len(args) <= 3:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "FIXED takes a number, optional decimals, "
                "and an optional no-commas flag"
            ),
        )
    number = to_number(
        evaluate(args[0], lookup, functions, names)
    )
    if is_error(number):
        return number
    decimals = _decimals_arg(
        args, 1, lookup, functions, names
    )
    if is_error(decimals):
        return decimals
    use_commas = True
    if len(args) == 3:
        flag = evaluate(args[2], lookup, functions, names)
        if is_error(flag):
            return flag
        use_commas = not bool(flag)
    return _format(number, decimals, use_commas)


DOLLAR_TEXT_FUNCTIONS = {
    "DOLLAR": _dollar,
    "FIXED": _fixed,
}
