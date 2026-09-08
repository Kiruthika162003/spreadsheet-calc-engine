"""Cell values: errors are values here, because the grid must keep working.

A spreadsheet cannot throw. One bad divisor in D7 must not
stop the other forty thousand cells from calculating, so
errors are first-class values, #DIV/0!, #VALUE!, #REF!,
#NAME?, #CYCLE!, that flow through arithmetic like any
number, poisoning exactly the cells that depend on them and
nothing else. The propagation rule is strict: any operation
touching an error yields that error, first error wins on
ties, because a formula that launders an error into a
plausible number is the spreadsheet failure with the
longest career, the one auditors write books about. Type
coercion is deliberately narrow: booleans count as 1 and 0
in arithmetic, text never silently becomes a number, and
empty cells are zero in sums but invisible in averages,
which is the one inconsistency users actually expect.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid

ERROR_CODES = (
    "#DIV/0!",
    "#VALUE!",
    "#REF!",
    "#NAME?",
    "#CYCLE!",
    "#NUM!",
)


@dataclass(frozen=True)
class ErrorValue:
    code: str
    note: str = ""

    def __post_init__(self) -> None:
        if self.code not in ERROR_CODES:
            raise Invalid(
                f"{self.code} is not a known error code; "
                "inventing error codes is how one bug becomes "
                "two"
            )

    def render(self) -> str:
        return self.code


Value = float | str | bool | ErrorValue | None


def is_error(value: Value) -> bool:
    return isinstance(value, ErrorValue)


def first_error(*values: Value) -> ErrorValue | None:
    for value in values:
        if isinstance(value, ErrorValue):
            return value
    return None


def to_number(value: Value) -> float | ErrorValue:
    if isinstance(value, ErrorValue):
        return value
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, float):
        return value
    if value is None:
        return 0.0
    return ErrorValue(
        code="#VALUE!",
        note=(
            f"text {value!r} does not silently become a "
            "number; laundered errors have the longest careers"
        ),
    )


def render(value: Value) -> str:
    if isinstance(value, ErrorValue):
        return value.render()
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        if value == int(value) and abs(value) < 1e15:
            return str(int(value))
        return repr(value)
    return value


def add(left: Value, right: Value) -> Value:
    poisoned = first_error(left, right)
    if poisoned:
        return poisoned
    left_number = to_number(left)
    right_number = to_number(right)
    poisoned = first_error(left_number, right_number)
    if poisoned:
        return poisoned
    return left_number + right_number


def subtract(left: Value, right: Value) -> Value:
    negated = multiply(right, -1.0)
    return add(left, negated)


def multiply(left: Value, right: Value) -> Value:
    poisoned = first_error(left, right)
    if poisoned:
        return poisoned
    left_number = to_number(left)
    right_number = to_number(right)
    poisoned = first_error(left_number, right_number)
    if poisoned:
        return poisoned
    return left_number * right_number


def divide(left: Value, right: Value) -> Value:
    poisoned = first_error(left, right)
    if poisoned:
        return poisoned
    left_number = to_number(left)
    right_number = to_number(right)
    poisoned = first_error(left_number, right_number)
    if poisoned:
        return poisoned
    if right_number == 0.0:
        return ErrorValue(
            code="#DIV/0!",
            note="the divisor is zero and the grid keeps working",
        )
    return left_number / right_number
