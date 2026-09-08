"""The second text family: find versus search, and joins that state their rules.

The incumbent ships two lookalike functions and a thousand
support tickets about the difference, so this family draws
the line in its own docstring: FIND is case-sensitive and
literal, SEARCH is case-blind and here also literal, the
wildcard support the incumbent hides inside SEARCH is
deliberately not copied, because a function that is
sometimes a pattern matcher depending on which characters
happen to be in the needle is two functions wearing one
name. Both return one-based positions and both refuse a
missing needle with #VALUE! rather than a sentinel, since
position zero is a lie waiting for arithmetic. SUBSTITUTE
replaces every occurrence unless the instance number picks
one, and an instance past the last occurrence changes
nothing, which is the difference between substitution and
wishful thinking. TEXTJOIN renders numbers the way the grid
renders them, skips empties only when told to, and joins
range contents in row-major order, the reading order of the
sheet. REPT refuses to build a cell longer than ten thousand
characters because a cell is not a novel, CHAR and CODE
speak printable ASCII and refuse the rest by number, and
VALUE parses what the lexer would call a number, no locale
guessing, since the locale module owns that war.
"""

from __future__ import annotations

from gridiron.ast import Range
from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    render,
    to_number,
)


def _text_arg(arg, lookup, functions, names) -> Value:
    value = evaluate(arg, lookup, functions, names)
    if is_error(value):
        return value
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return render(value)


def _number_arg(arg, lookup, functions, names) -> Value:
    value = evaluate(arg, lookup, functions, names)
    if is_error(value):
        return value
    return to_number(value)


def _substitute(args, lookup, functions, names) -> Value:
    if len(args) not in (3, 4):
        return ErrorValue(
            code="#VALUE!",
            note=(
                "SUBSTITUTE takes text, old, new, and an "
                "optional instance"
            ),
        )
    gathered = []
    for arg in args[:3]:
        text = _text_arg(arg, lookup, functions, names)
        if is_error(text):
            return text
        gathered.append(text)
    haystack, old, new = gathered
    if old == "":
        return haystack
    if len(args) == 3:
        return haystack.replace(old, new)
    instance_value = _number_arg(
        args[3], lookup, functions, names
    )
    if is_error(instance_value):
        return instance_value
    instance = int(instance_value)
    if instance < 1:
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"instance {instance} does not exist; "
                "occurrences count from one"
            ),
        )
    position = -1
    for _ in range(instance):
        position = haystack.find(old, position + 1)
        if position == -1:
            return haystack
    return (
        haystack[:position]
        + new
        + haystack[position + len(old) :]
    )


def _replace(args, lookup, functions, names) -> Value:
    if len(args) != 4:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "REPLACE takes text, start, count, and "
                "new text"
            ),
        )
    haystack = _text_arg(args[0], lookup, functions, names)
    if is_error(haystack):
        return haystack
    start_value = _number_arg(
        args[1], lookup, functions, names
    )
    if is_error(start_value):
        return start_value
    count_value = _number_arg(
        args[2], lookup, functions, names
    )
    if is_error(count_value):
        return count_value
    new = _text_arg(args[3], lookup, functions, names)
    if is_error(new):
        return new
    start = int(start_value)
    count = int(count_value)
    if start < 1 or count < 0:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "REPLACE positions are one-based and "
                "counts are not negative"
            ),
        )
    index = start - 1
    return haystack[:index] + new + haystack[index + count :]


def _finder(label: str, fold_case: bool):
    def run(args, lookup, functions, names) -> Value:
        if len(args) not in (2, 3):
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"{label} takes a needle, a haystack, "
                    "and an optional start"
                ),
            )
        needle = _text_arg(
            args[0], lookup, functions, names
        )
        if is_error(needle):
            return needle
        haystack = _text_arg(
            args[1], lookup, functions, names
        )
        if is_error(haystack):
            return haystack
        start = 1
        if len(args) == 3:
            start_value = _number_arg(
                args[2], lookup, functions, names
            )
            if is_error(start_value):
                return start_value
            start = int(start_value)
        if start < 1 or start > len(haystack) + 1:
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"{label} start {start} is outside the "
                    "haystack"
                ),
            )
        if fold_case:
            position = haystack.upper().find(
                needle.upper(), start - 1
            )
        else:
            position = haystack.find(needle, start - 1)
        if position == -1:
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"{label} did not find {needle!r}; "
                    "position zero is a lie waiting for "
                    "arithmetic"
                ),
            )
        return float(position + 1)

    return run


def _rept(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="REPT takes text and a count",
        )
    text = _text_arg(args[0], lookup, functions, names)
    if is_error(text):
        return text
    count_value = _number_arg(
        args[1], lookup, functions, names
    )
    if is_error(count_value):
        return count_value
    count = int(count_value)
    if count < 0:
        return ErrorValue(
            code="#VALUE!",
            note="REPT cannot repeat a negative number "
            "of times",
        )
    if len(text) * count > 10000:
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"{len(text) * count} characters; a cell "
                "is not a novel"
            ),
        )
    return text * count


def _textjoin(args, lookup, functions, names) -> Value:
    if len(args) < 3:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "TEXTJOIN takes a delimiter, a skip-empty "
                "flag, and values"
            ),
        )
    delimiter = _text_arg(
        args[0], lookup, functions, names
    )
    if is_error(delimiter):
        return delimiter
    flag = evaluate(args[1], lookup, functions, names)
    if is_error(flag):
        return flag
    if not isinstance(flag, bool):
        return ErrorValue(
            code="#VALUE!",
            note=(
                "the skip-empty flag is TRUE or FALSE, "
                "stated, not implied"
            ),
        )
    pieces: list[str] = []
    for arg in args[2:]:
        if isinstance(arg, Range):
            for cell in arg.ref.cells():
                value = lookup(cell)
                if is_error(value):
                    return value
                if value is None:
                    if not flag:
                        pieces.append("")
                    continue
                pieces.append(
                    value
                    if isinstance(value, str)
                    else render(value)
                )
        else:
            text = _text_arg(
                arg, lookup, functions, names
            )
            if is_error(text):
                return text
            if text == "" and flag:
                continue
            pieces.append(text)
    return delimiter.join(pieces)


def _proper(args, lookup, functions, names) -> Value:
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!", note="PROPER takes one text"
        )
    text = _text_arg(args[0], lookup, functions, names)
    if is_error(text):
        return text
    result = []
    boundary = True
    for char in text:
        if char.isalpha():
            result.append(
                char.upper() if boundary else char.lower()
            )
            boundary = False
        else:
            result.append(char)
            boundary = True
    return "".join(result)


def _exact(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!", note="EXACT takes two texts"
        )
    left = _text_arg(args[0], lookup, functions, names)
    if is_error(left):
        return left
    right = _text_arg(args[1], lookup, functions, names)
    if is_error(right):
        return right
    return left == right


def _char(args, lookup, functions, names) -> Value:
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!", note="CHAR takes one code"
        )
    code_value = _number_arg(
        args[0], lookup, functions, names
    )
    if is_error(code_value):
        return code_value
    code = int(code_value)
    if not 32 <= code <= 126:
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"code {code} is outside printable ASCII "
                "(32 to 126)"
            ),
        )
    return chr(code)


def _code(args, lookup, functions, names) -> Value:
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!", note="CODE takes one text"
        )
    text = _text_arg(args[0], lookup, functions, names)
    if is_error(text):
        return text
    if not text:
        return ErrorValue(
            code="#VALUE!",
            note="CODE of empty text has no first character",
        )
    first = ord(text[0])
    if not 32 <= first <= 126:
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"character {text[0]!r} is outside "
                "printable ASCII (32 to 126)"
            ),
        )
    return float(first)


def _value(args, lookup, functions, names) -> Value:
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!", note="VALUE takes one text"
        )
    text = _text_arg(args[0], lookup, functions, names)
    if is_error(text):
        return text
    try:
        return float(text.strip())
    except ValueError:
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"{text!r} is not a number the lexer would "
                "recognize; the locale module owns that war"
            ),
        )


TEXT_EXTRA_FUNCTIONS = {
    "SUBSTITUTE": _substitute,
    "REPLACE": _replace,
    "FIND": _finder("FIND", fold_case=False),
    "SEARCH": _finder("SEARCH", fold_case=True),
    "REPT": _rept,
    "TEXTJOIN": _textjoin,
    "PROPER": _proper,
    "EXACT": _exact,
    "CHAR": _char,
    "CODE": _code,
    "VALUE": _value,
}
