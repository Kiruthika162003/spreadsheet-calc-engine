"""Engineering: base conversions with the incumbent's ten-bit two's complement.

The base-conversion functions carry one piece of history that
must be preserved or every imported engineering sheet breaks:
the string forms are ten bits wide and negative numbers use
two's complement, so DEC2BIN(-1) is 1111111111 and the
representable range is exactly -512 to 511. That is not the
range a naive implementation would pick, and picking a
friendlier one silently would make this engine disagree with
the files it exists to read, so the range is enforced and its
overflow is refused with both bounds named. The text-to-
number direction reads the same ten-bit convention back,
treating a leading one in a full-width string as the sign
bit, and refuses a digit that does not belong to the base,
an eight in a binary string, rather than skipping it, because
a silently dropped digit is a wrong number that looks right.
The bitwise operators work on non-negative integers only and
say so, since two's complement makes bitwise-and of negatives
a question about width that the spreadsheet functions never
answered consistently, and refusing is more honest than
inventing a forty-eighth bit nobody asked for.
"""

from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)

_WIDTH = 10
_MODULUS = 1 << _WIDTH
_MIN = -(_MODULUS // 2)
_MAX = _MODULUS // 2 - 1
_DIGITS = "0123456789ABCDEF"


def _int(arg, lookup, functions, names):
    value = to_number(
        evaluate(arg, lookup, functions, names)
    )
    if is_error(value):
        return value
    if value != int(value):
        return ErrorValue(
            code="#NUM!",
            note=f"{value} is not a whole number",
        )
    return int(value)


def _to_base(base: int, label: str):
    def run(args, lookup, functions, names) -> Value:
        if len(args) != 1:
            return ErrorValue(
                code="#VALUE!",
                note=f"{label} takes one number",
            )
        number = _int(args[0], lookup, functions, names)
        if is_error(number):
            return number
        if not _MIN <= number <= _MAX:
            return ErrorValue(
                code="#NUM!",
                note=(
                    f"{label} holds {_WIDTH} bits, range "
                    f"{_MIN} to {_MAX}; {number} overflows it"
                ),
            )
        residue = number % _MODULUS
        if residue == 0:
            return "0"
        digits = ""
        while residue:
            digits = _DIGITS[residue % base] + digits
            residue //= base
        return digits

    return run


def _from_base(base: int, label: str):
    def run(args, lookup, functions, names) -> Value:
        if len(args) != 1:
            return ErrorValue(
                code="#VALUE!",
                note=f"{label} takes one text",
            )
        text = evaluate(args[0], lookup, functions, names)
        if is_error(text):
            return text
        if isinstance(text, float) and not isinstance(
            text, bool
        ):
            text = str(int(text))
        if not isinstance(text, str) or not text:
            return ErrorValue(
                code="#VALUE!",
                note=f"{label} needs a non-empty string",
            )
        upper = text.upper()
        for char in upper:
            if (
                char not in _DIGITS
                or _DIGITS.index(char) >= base
            ):
                return ErrorValue(
                    code="#NUM!",
                    note=(
                        f"{char!r} is not a base-{base} "
                        "digit; a dropped digit is a wrong "
                        "number that looks right"
                    ),
                )
        value = int(upper, base)
        if len(upper) == _WIDTH and value >= _MODULUS // 2:
            value -= _MODULUS
        return float(value)

    return run


def _bitwise(op, label: str):
    def run(args, lookup, functions, names) -> Value:
        if len(args) != 2:
            return ErrorValue(
                code="#VALUE!",
                note=f"{label} takes two numbers",
            )
        left = _int(args[0], lookup, functions, names)
        if is_error(left):
            return left
        right = _int(args[1], lookup, functions, names)
        if is_error(right):
            return right
        if left < 0 or right < 0:
            return ErrorValue(
                code="#NUM!",
                note=(
                    f"{label} works on non-negative "
                    "integers; two's complement of a "
                    "negative is a question about width"
                ),
            )
        return float(op(left, right))

    return run


ENGINEERING_FUNCTIONS = {
    "DEC2BIN": _to_base(2, "DEC2BIN"),
    "DEC2OCT": _to_base(8, "DEC2OCT"),
    "DEC2HEX": _to_base(16, "DEC2HEX"),
    "BIN2DEC": _from_base(2, "BIN2DEC"),
    "OCT2DEC": _from_base(8, "OCT2DEC"),
    "HEX2DEC": _from_base(16, "HEX2DEC"),
    "BITAND": _bitwise(lambda a, b: a & b, "BITAND"),
    "BITOR": _bitwise(lambda a, b: a | b, "BITOR"),
    "BITXOR": _bitwise(lambda a, b: a ^ b, "BITXOR"),
}
