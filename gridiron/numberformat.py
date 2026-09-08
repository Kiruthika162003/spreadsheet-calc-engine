"""Number formats: the value never changes, only its clothes.

A format code is a rendering instruction, never a rounding
of storage: the cell holds 2.71828 while "0.00" displays
2.72, and arithmetic downstream uses the full value, which
is the rule half of all spreadsheet support tickets turn on,
"the totals do not match what I see". This renderer covers
the working core of the code language: zeros force digits,
hashes allow them, the comma groups thousands, the percent
sign multiplies the display by a hundred and appends itself,
and a negative section after a semicolon takes over for
negative values, parentheses style. Codes it does not know
are refused at parse time with the code quoted, because
rendering something for an unrecognized code would mean
guessing what the author meant about money.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.values import Value, render

_ALLOWED = set("0#.,%();-")


@dataclass(frozen=True)
class NumberFormat:
    code: str
    positive: str
    negative: str | None

    @classmethod
    def parse(cls, code: str) -> NumberFormat:
        if not code:
            raise Invalid("an empty format code dresses nothing")
        for char in code:
            if char not in _ALLOWED:
                raise Invalid(
                    f"format code {code!r} contains {char!r}, "
                    "which this renderer does not know; "
                    "guessing what an author meant about "
                    "money is refused"
                )
        sections = code.split(";")
        if len(sections) > 2:
            raise Invalid(
                "at most two sections, positive and negative"
            )
        return cls(
            code=code,
            positive=sections[0],
            negative=sections[1]
            if len(sections) == 2
            else None,
        )

    def _decimals(self, section: str) -> int:
        if "." not in section:
            return 0
        return sum(
            1
            for char in section.split(".", 1)[1]
            if char in "0#"
        )

    def _render_section(
        self, magnitude: float, section: str
    ) -> str:
        percent = "%" in section
        if percent:
            magnitude *= 100
        decimals = self._decimals(section)
        grouped = "," in section
        text = f"{magnitude:.{decimals}f}"
        if grouped:
            whole, _, frac = text.partition(".")
            whole = f"{int(whole):,}"
            text = whole + ("." + frac if frac else "")
        if percent:
            text += "%"
        if "(" in section and ")" in section:
            text = f"({text})"
        return text

    def apply(self, value: Value) -> str:
        if not isinstance(value, float) or isinstance(
            value, bool
        ):
            return render(value)
        if value < 0 and self.negative is not None:
            return self._render_section(
                -value, self.negative
            )
        if value < 0:
            return "-" + self._render_section(
                -value, self.positive
            )
        return self._render_section(value, self.positive)
