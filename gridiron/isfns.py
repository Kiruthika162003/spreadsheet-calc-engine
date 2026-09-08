"""The IS family: questions about values that never become errors themselves.

ISERROR exists to look at an error without flinching, so the
one rule of this family is that no IS function ever returns
an error: they answer TRUE or FALSE about whatever arrives,
including the arrival of #DIV/0! itself, because an
inspector that faints at the sight of what it inspects
protects nothing. ISBLANK is the honest test the criteria
module keeps pointing at, true only for the truly absent
cell, not for empty text, which is the distinction between a
cell nobody touched and a cell somebody emptied, and the
two mean different things in every audit. ISNUMBER says no
to booleans even though arithmetic coerces them, because the
question is what the value is, not what it could be talked
into.
"""

from __future__ import annotations

from gridiron.ast import Ref
from gridiron.evaluate import evaluate
from gridiron.values import ErrorValue, Value, is_error


def _subject(args, lookup, functions, names) -> Value:
    return evaluate(args[0], lookup, functions, names)


def _one_arg(name: str, answer):
    def run(args, lookup, functions, names) -> Value:
        if len(args) != 1:
            return ErrorValue(
                code="#VALUE!",
                note=f"{name} takes one value",
            )
        return answer(
            _subject(args, lookup, functions, names)
        )

    return run


def _isblank(args, lookup, functions, names) -> Value:
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!", note="ISBLANK takes one cell"
        )
    if isinstance(args[0], Ref):
        return lookup(args[0].ref) is None
    return _subject(args, lookup, functions, names) is None


IS_FUNCTIONS = {
    "ISBLANK": _isblank,
    "ISNUMBER": _one_arg(
        "ISNUMBER",
        lambda value: isinstance(value, float)
        and not isinstance(value, bool),
    ),
    "ISTEXT": _one_arg(
        "ISTEXT", lambda value: isinstance(value, str)
    ),
    "ISLOGICAL": _one_arg(
        "ISLOGICAL", lambda value: isinstance(value, bool)
    ),
    "ISERROR": _one_arg("ISERROR", is_error),
}
