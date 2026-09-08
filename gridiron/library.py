"""The full function library: one lookup over every family."""

from __future__ import annotations

from gridiron.conditionalfns import CONDITIONAL_FUNCTIONS
from gridiron.datefns import DATE_FUNCTIONS
from gridiron.datextra import DATE_EXTRA_FUNCTIONS
from gridiron.engineering import ENGINEERING_FUNCTIONS
from gridiron.financeextra import FINANCE_EXTRA_FUNCTIONS
from gridiron.financefns import FINANCE_FUNCTIONS
from gridiron.functions import BUILTINS
from gridiron.isfns import IS_FUNCTIONS
from gridiron.letfns import LET_FUNCTIONS
from gridiron.logicfns import LOGIC_FUNCTIONS
from gridiron.logicmore import LOGIC_MORE_FUNCTIONS
from gridiron.lookupextra import LOOKUP_EXTRA_FUNCTIONS
from gridiron.lookupfns import LOOKUP_FUNCTIONS
from gridiron.mathextra import MATH_EXTRA_FUNCTIONS
from gridiron.mathfns import MATH_FUNCTIONS
from gridiron.mathmore import MATH_MORE_FUNCTIONS
from gridiron.multicriteria import MULTICRITERIA_FUNCTIONS
from gridiron.queryfns import QUERY_FUNCTIONS
from gridiron.rankfns import RANK_FUNCTIONS
from gridiron.regression import REGRESSION_FUNCTIONS
from gridiron.statfns import STAT_FUNCTIONS
from gridiron.textextra import TEXT_EXTRA_FUNCTIONS
from gridiron.textfns import TEXT_FUNCTIONS
from gridiron.textmore import TEXT_MORE_FUNCTIONS
from gridiron.units import UNIT_FUNCTIONS

_FAMILIES = (
    BUILTINS,
    TEXT_FUNCTIONS,
    TEXT_EXTRA_FUNCTIONS,
    TEXT_MORE_FUNCTIONS,
    LOGIC_FUNCTIONS,
    LOGIC_MORE_FUNCTIONS,
    LOOKUP_FUNCTIONS,
    LOOKUP_EXTRA_FUNCTIONS,
    CONDITIONAL_FUNCTIONS,
    MULTICRITERIA_FUNCTIONS,
    DATE_FUNCTIONS,
    DATE_EXTRA_FUNCTIONS,
    STAT_FUNCTIONS,
    RANK_FUNCTIONS,
    REGRESSION_FUNCTIONS,
    QUERY_FUNCTIONS,
    FINANCE_FUNCTIONS,
    FINANCE_EXTRA_FUNCTIONS,
    MATH_FUNCTIONS,
    MATH_EXTRA_FUNCTIONS,
    MATH_MORE_FUNCTIONS,
    ENGINEERING_FUNCTIONS,
    UNIT_FUNCTIONS,
    IS_FUNCTIONS,
    LET_FUNCTIONS,
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
