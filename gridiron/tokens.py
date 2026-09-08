"""The formula lexer: characters become tokens, and position is part of truth.

Every token remembers where it started, because a parse error
that says "unexpected token" is a shrug and one that says
"unexpected ) at position 14" is a fix. The lexer knows the
whole surface of the formula language: numbers with decimals,
quoted strings with doubled-quote escapes, cell and range
references left as words for the parser to classify,
function names, the operator set, and the argument separator.
Ambiguity is resolved at the character level in exactly one
place, the longest-match rule for two-character operators,
so <= is one token and never a less-than followed by a
mystery. Unknown characters fail immediately with the
character and position named, since a lexer that skips what
it does not understand is an autocorrect, and autocorrect is
the one feature no formula bar should ever have.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Unparseable

TWO_CHAR_OPERATORS = ("<=", ">=", "<>")
ONE_CHAR_OPERATORS = "+-*/^%&<>=(),:"
KIND_NUMBER = "number"
KIND_STRING = "string"
KIND_WORD = "word"
KIND_OPERATOR = "operator"


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    position: int


def _lex_string(formula: str, start: int) -> tuple[Token, int]:
    index = start + 1
    length = len(formula)
    body = []
    while index < length:
        if formula[index] == '"':
            if index + 1 < length and formula[index + 1] == '"':
                body.append('"')
                index += 2
                continue
            return (
                Token(
                    kind=KIND_STRING,
                    text="".join(body),
                    position=start,
                ),
                index + 1,
            )
        body.append(formula[index])
        index += 1
    raise Unparseable(
        f"the string opened at position {start} never closes"
    )


def _lex_number(formula: str, start: int) -> tuple[Token, int]:
    index = start
    length = len(formula)
    seen_dot = False
    while index < length and (
        formula[index].isdigit()
        or (formula[index] == "." and not seen_dot)
    ):
        seen_dot = seen_dot or formula[index] == "."
        index += 1
    return (
        Token(
            kind=KIND_NUMBER,
            text=formula[start:index],
            position=start,
        ),
        index,
    )


def lex(formula: str) -> list[Token]:
    if not formula.strip():
        raise Unparseable("an empty formula parses to nothing")
    tokens: list[Token] = []
    index = 0
    length = len(formula)
    while index < length:
        char = formula[index]
        if char == " ":
            index += 1
            continue
        two = formula[index : index + 2]
        if two in TWO_CHAR_OPERATORS:
            tokens.append(
                Token(kind=KIND_OPERATOR, text=two, position=index)
            )
            index += 2
            continue
        if char in ONE_CHAR_OPERATORS:
            tokens.append(
                Token(
                    kind=KIND_OPERATOR, text=char, position=index
                )
            )
            index += 1
            continue
        if char.isdigit() or (
            char == "."
            and index + 1 < length
            and formula[index + 1].isdigit()
        ):
            token, index = _lex_number(formula, index)
            tokens.append(token)
            continue
        if char == '"':
            token, index = _lex_string(formula, index)
            tokens.append(token)
            continue
        if char.isalpha() or char in "$_":
            start = index
            while index < length and (
                formula[index].isalnum()
                or formula[index] in "$_."
            ):
                index += 1
            tokens.append(
                Token(
                    kind=KIND_WORD,
                    text=formula[start:index],
                    position=start,
                )
            )
            continue
        raise Unparseable(
            f"unexpected character {char!r} at position "
            f"{index}; a lexer that skips what it does not "
            "understand is an autocorrect"
        )
    return tokens
