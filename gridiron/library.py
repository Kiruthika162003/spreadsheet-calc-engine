"""The full function library: one lookup over every family."""

from __future__ import annotations

from gridiron.functions import BUILTINS
from gridiron.textfns import TEXT_FUNCTIONS


def full_table(name: str):
    found = BUILTINS.get(name)
    if found is not None:
        return found
    return TEXT_FUNCTIONS.get(name)


def catalog() -> list[str]:
    return sorted({*BUILTINS, *TEXT_FUNCTIONS})
