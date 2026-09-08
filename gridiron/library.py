"""The full function library: one lookup over every family."""

from __future__ import annotations

from gridiron.conditionalfns import CONDITIONAL_FUNCTIONS
from gridiron.datefns import DATE_FUNCTIONS
from gridiron.functions import BUILTINS
from gridiron.logicfns import LOGIC_FUNCTIONS
from gridiron.lookupfns import LOOKUP_FUNCTIONS
from gridiron.textfns import TEXT_FUNCTIONS

_FAMILIES = (
    BUILTINS,
    TEXT_FUNCTIONS,
    LOGIC_FUNCTIONS,
    LOOKUP_FUNCTIONS,
    CONDITIONAL_FUNCTIONS,
    DATE_FUNCTIONS,
)


def full_table(name: str):
    for family in _FAMILIES:
        found = family.get(name)
        if found is not None:
            return found
    return None


def catalog() -> list[str]:
    names: set[str] = set()
    for family in _FAMILIES:
        names.update(family)
    return sorted(names)
