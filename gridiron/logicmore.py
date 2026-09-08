"""More logic: the multi-branch functions, each lazy where laziness is correctness.

IF chooses between two branches; the functions here choose
among many, and the shared discipline is laziness: only the
selected branch is evaluated, because a multi-branch function
that eagerly evaluated every arm would fire the side effect
or trip the error in a branch it was never going to take. IFS
walks condition-and-value pairs and returns the value of the
first true condition, evaluating conditions in order and
stopping at the first hit, so a later condition that would
error is never reached if an earlier one wins, and a run
where no condition is true is #N/A rather than a silent
blank, because falling through every case unmatched is a
question the sheet author did not finish answering. SWITCH
compares one expression against a list of candidates and
returns the match's result, with an optional trailing
default, and it evaluates the expression exactly once rather
than per candidate, matching LET's once-only promise for the
same reason. CHOOSE indexes a one-based list and evaluates
only the chosen entry, refusing an index outside the list
rather than clamping, because CHOOSE(5, a, b) is an
off-by-something the caller needs told, not the last entry
handed back as if it were meant. IFNA is IFERROR narrowed to
exactly #N/A, because catching every error to handle a
missing lookup also swallows the #REF! that means something
entirely different and should not be hidden.
"""

from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.values import ErrorValue, Value, is_error


def _ifs(args, lookup, functions, names) -> Value:
    if not args or len(args) % 2 == 1:
        return ErrorValue(
            code="#VALUE!",
            note="IFS takes condition and value pairs",
        )
    for cond_arg, value_arg in zip(
        args[0::2], args[1::2], strict=True
    ):
        condition = evaluate(
            cond_arg, lookup, functions, names
        )
        if is_error(condition):
            return condition
        if condition is True or (
            isinstance(condition, float)
            and condition != 0
        ):
            return evaluate(
                value_arg, lookup, functions, names
            )
    return ErrorValue(
        code="#N/A",
        note=(
            "no condition was true; falling through every "
            "case unmatched is a question left unfinished"
        ),
    )


def _switch(args, lookup, functions, names) -> Value:
    if len(args) < 3:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "SWITCH takes an expression, then "
                "value/result pairs, then an optional default"
            ),
        )
    subject = evaluate(args[0], lookup, functions, names)
    if is_error(subject):
        return subject
    rest = args[1:]
    has_default = len(rest) % 2 == 1
    pairs = rest[:-1] if has_default else rest
    for candidate_arg, result_arg in zip(
        pairs[0::2], pairs[1::2], strict=True
    ):
        candidate = evaluate(
            candidate_arg, lookup, functions, names
        )
        if is_error(candidate):
            return candidate
        if _equal(subject, candidate):
            return evaluate(
                result_arg, lookup, functions, names
            )
    if has_default:
        return evaluate(
            rest[-1], lookup, functions, names
        )
    return ErrorValue(
        code="#N/A",
        note=(
            "no candidate matched and no default was given"
        ),
    )


def _equal(left: Value, right: Value) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return left.upper() == right.upper()
    return left == right


def _choose(args, lookup, functions, names) -> Value:
    if len(args) < 2:
        return ErrorValue(
            code="#VALUE!",
            note="CHOOSE takes an index and at least one value",
        )
    index_value = evaluate(
        args[0], lookup, functions, names
    )
    if is_error(index_value):
        return index_value
    if not isinstance(index_value, float) or isinstance(
        index_value, bool
    ):
        return ErrorValue(
            code="#VALUE!",
            note="CHOOSE needs a numeric index",
        )
    index = int(index_value)
    choices = args[1:]
    if not 1 <= index <= len(choices):
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"CHOOSE index {index} is outside 1 to "
                f"{len(choices)}; a clamp would hand back "
                "an entry the caller did not mean"
            ),
        )
    return evaluate(
        choices[index - 1], lookup, functions, names
    )


def _ifna(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="IFNA takes a value and a fallback",
        )
    value = evaluate(args[0], lookup, functions, names)
    if is_error(value) and value.code == "#N/A":
        return evaluate(
            args[1], lookup, functions, names
        )
    return value


LOGIC_MORE_FUNCTIONS = {
    "IFS": _ifs,
    "SWITCH": _switch,
    "CHOOSE": _choose,
    "IFNA": _ifna,
}
