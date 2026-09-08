"""Rich text: styled runs inside one string, with the text always recoverable.

A rich-text cell is a string wearing formatting on stretches
of itself, one word bold, a phrase in red, and the invariant
that keeps it honest is that the plain text is always the
concatenation of the runs in order, unstyled. Formatting is a
layer over characters, never a rewrite of them, so extracting
the plain text of a rich cell gives exactly what a formula
referencing that cell would see, and a rich cell and a plain
cell holding the same words compare equal as values because
the words are the value and the styling is decoration. Runs
are stored as adjacent, non-overlapping spans covering the
whole string with no gaps, because a gap would be characters
belonging to no run and an overlap would be a character
wearing two conflicting styles, and both are corruption a
renderer cannot resolve. Applying a style to a character
range splits the runs at the range boundaries and restyles
the middle, then merges any adjacent runs that ended up
identical, so the run list stays minimal and a round of
bolding then unbolding returns to a single plain run rather
than leaving three runs that happen to look the same. A range
outside the string is refused rather than silently clamped,
because styling characters that do not exist is a bug in the
caller that a clamp would hide.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    color: str = "default"

    def style(self) -> tuple:
        return (self.bold, self.italic, self.color)


@dataclass
class RichText:
    runs: list[Run] = field(default_factory=list)

    @classmethod
    def plain(cls, text: str) -> RichText:
        if not text:
            return cls(runs=[])
        return cls(runs=[Run(text=text)])

    def text(self) -> str:
        return "".join(run.text for run in self.runs)

    def _rebuild(
        self, styled: list[tuple[str, tuple]]
    ) -> None:
        merged: list[Run] = []
        for char, style in styled:
            if merged and merged[-1].style() == style:
                previous = merged[-1]
                merged[-1] = Run(
                    text=previous.text + char,
                    bold=style[0],
                    italic=style[1],
                    color=style[2],
                )
            else:
                merged.append(
                    Run(
                        text=char,
                        bold=style[0],
                        italic=style[1],
                        color=style[2],
                    )
                )
        self.runs = merged

    def _explode(self) -> list[tuple[str, tuple]]:
        chars = []
        for run in self.runs:
            for char in run.text:
                chars.append((char, run.style()))
        return chars

    def apply(
        self,
        start: int,
        end: int,
        *,
        bold: bool | None = None,
        italic: bool | None = None,
        color: str | None = None,
    ) -> None:
        chars = self._explode()
        if not 0 <= start < end <= len(chars):
            raise Invalid(
                f"range [{start}, {end}) is outside the "
                f"{len(chars)}-character string; styling "
                "characters that do not exist is a caller bug"
            )
        for index in range(start, end):
            char, (was_bold, was_italic, was_color) = chars[
                index
            ]
            chars[index] = (
                char,
                (
                    was_bold if bold is None else bold,
                    was_italic
                    if italic is None
                    else italic,
                    was_color if color is None else color,
                ),
            )
        self._rebuild(chars)

    def run_count(self) -> int:
        return len(self.runs)
