"""Criteria strings: the tiny language inside COUNTIF, parsed once, honestly.

">100", "<>done", "app*": conditional aggregation runs on a
micro-grammar that most engines re-parse per cell, per call,
which is how a COUNTIF over ten thousand rows spends its time
in string handling. Here a criterion parses once into a
predicate: an optional comparison operator, then either a
number or text, with * and ? wildcards compiled to a pattern
when the text form carries them. The semantics keep the
incumbent's two defensible quirks and refuse the third: bare
text means equals, wildcards are case-insensitive like all
text comparison here, but a criterion that is an empty
string is refused rather than matching empties, because
"count the cells equal to nothing" deserves an explicit
ISBLANK, not a silent convention nobody can look up.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.values import Value

_OPERATORS = ("<>", "<=", ">=", "<", ">", "=")

Predicate = Callable[[Value], bool]


def _numeric_test(op: str, target: float) -> Predicate:
    def test(value: Value) -> bool:
        if not isinstance(value, float) or isinstance(
            value, bool
        ):
            return op == "<>"
        if op == "=":
            return value == target
        if op == "<>":
            return value != target
        if op == "<":
            return value < target
        if op == "<=":
            return value <= target
        if op == ">":
            return value > target
        return value >= target

    return test


def _text_test(op: str, target: str) -> Predicate:
    folded = target.upper()
    if "*" in folded or "?" in folded:
        pattern = re.escape(folded)
        pattern = pattern.replace(r"\*", ".*")
        pattern = pattern.replace(r"\?", ".")
        compiled = re.compile(f"^{pattern}$")

        def wildcard_test(value: Value) -> bool:
            matched = isinstance(value, str) and bool(
                compiled.match(value.upper())
            )
            return not matched if op == "<>" else matched

        if op not in ("=", "<>"):
            raise Invalid(
                f"wildcards only combine with = or <>, not "
                f"{op}"
            )
        return wildcard_test

    def test(value: Value) -> bool:
        is_match = (
            isinstance(value, str)
            and value.upper() == folded
        )
        return not is_match if op == "<>" else is_match

    if op not in ("=", "<>"):
        raise Invalid(
            f"text criteria only combine with = or <>, not {op}"
        )
    return test


@dataclass(frozen=True)
class Criterion:
    source: str
    predicate: Predicate

    @classmethod
    def parse(cls, text: str) -> Criterion:
        if not text:
            raise Invalid(
                "the empty criterion is refused; count the "
                "cells equal to nothing deserves an explicit "
                "ISBLANK, not a silent convention"
            )
        op = "="
        body = text
        for candidate in _OPERATORS:
            if text.startswith(candidate):
                op = candidate
                body = text[len(candidate) :]
                break
        try:
            target = float(body)
        except ValueError:
            return cls(
                source=text,
                predicate=_text_test(op, body),
            )
        return cls(
            source=text, predicate=_numeric_test(op, target)
        )

    def matches(self, value: Value) -> bool:
        return self.predicate(value)
