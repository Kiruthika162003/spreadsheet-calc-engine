"""The parser: Excel's precedence, including the part everyone argues about.

Precedence climbs from comparisons through concatenation,
addition, multiplication, exponentiation, and unary minus,
and the famous case is settled the way the incumbent settled
it: unary minus binds tighter than the caret, so -2^2 is 4,
not -4. Mathematics disagrees, thirty years of shipped
workbooks do not care, and an engine that silently fixed the
sign would change the value of cells it never met. Percent
is a postfix that divides by a hundred and stacks, function
calls take comma-separated arguments, and every syntax error
names its position, because the parser inherits the lexer's
oath: no shrugs, no autocorrect, coordinates always.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.ast import (
    Binary,
    Bool,
    Call,
    Name,
    Node,
    Number,
    Range,
    Ref,
    Text,
    Unary,
    XRef,
)
from gridiron.errors import Invalid, Unparseable
from gridiron.refs import CellRef, RangeRef
from gridiron.tokens import (
    KIND_NUMBER,
    KIND_OPERATOR,
    KIND_STRING,
    KIND_WORD,
    Token,
    lex,
)

COMPARISONS = ("=", "<>", "<", "<=", ">", ">=")


@dataclass
class Parser:
    tokens: list[Token]
    index: int = field(default=0)

    def peek(self) -> Token | None:
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        return None

    def take(self) -> Token:
        token = self.peek()
        if token is None:
            raise Unparseable(
                "the formula ends where more was expected"
            )
        self.index += 1
        return token

    def expect(self, text: str) -> None:
        token = self.take()
        if token.kind != KIND_OPERATOR or token.text != text:
            raise Unparseable(
                f"expected {text!r} at position "
                f"{token.position}, found {token.text!r}"
            )

    def at_operator(self, *texts: str) -> bool:
        token = self.peek()
        return (
            token is not None
            and token.kind == KIND_OPERATOR
            and token.text in texts
        )

    def parse(self) -> Node:
        node = self.comparison()
        leftover = self.peek()
        if leftover is not None:
            raise Unparseable(
                f"unexpected {leftover.text!r} at position "
                f"{leftover.position}; the formula was already "
                "complete"
            )
        return node

    def comparison(self) -> Node:
        node = self.concat()
        while self.at_operator(*COMPARISONS):
            op = self.take().text
            node = Binary(op=op, left=node, right=self.concat())
        return node

    def concat(self) -> Node:
        node = self.additive()
        while self.at_operator("&"):
            self.take()
            node = Binary(
                op="&", left=node, right=self.additive()
            )
        return node

    def additive(self) -> Node:
        node = self.multiplicative()
        while self.at_operator("+", "-"):
            op = self.take().text
            node = Binary(
                op=op, left=node, right=self.multiplicative()
            )
        return node

    def multiplicative(self) -> Node:
        node = self.power()
        while self.at_operator("*", "/"):
            op = self.take().text
            node = Binary(op=op, left=node, right=self.power())
        return node

    def power(self) -> Node:
        node = self.unary()
        while self.at_operator("^"):
            self.take()
            node = Binary(op="^", left=node, right=self.unary())
        return node

    def unary(self) -> Node:
        if self.at_operator("-"):
            self.take()
            return Unary(op="-", operand=self.unary())
        if self.at_operator("+"):
            self.take()
            return self.unary()
        return self.postfix()

    def postfix(self) -> Node:
        node = self.primary()
        while self.at_operator("%"):
            self.take()
            node = Binary(
                op="/", left=node, right=Number(value=100.0)
            )
        return node

    def primary(self) -> Node:
        token = self.take()
        if token.kind == KIND_NUMBER:
            return Number(value=float(token.text))
        if token.kind == KIND_STRING:
            return Text(value=token.text)
        if token.kind == KIND_OPERATOR and token.text == "(":
            inner = self.comparison()
            self.expect(")")
            return inner
        if token.kind == KIND_WORD:
            return self.word(token)
        raise Unparseable(
            f"unexpected {token.text!r} at position "
            f"{token.position}"
        )

    def word(self, token: Token) -> Node:
        upper = token.text.upper()
        if "!" in upper:
            sheet_name, _, ref_text = upper.partition("!")
            if not sheet_name or not ref_text:
                raise Unparseable(
                    f"a sheet reference needs both halves at "
                    f"position {token.position}"
                )
            if self.at_operator(":"):
                raise Unparseable(
                    "cross-sheet ranges are not supported; "
                    "pull the range onto one sheet and "
                    "reference the result"
                )
            try:
                target = CellRef.parse(ref_text)
            except Invalid as refusal:
                raise Unparseable(str(refusal)) from refusal
            return XRef(sheet=sheet_name, ref=target)
        if upper in ("TRUE", "FALSE"):
            return Bool(value=upper == "TRUE")
        if self.at_operator("("):
            self.take()
            args: list[Node] = []
            if not self.at_operator(")"):
                args.append(self.comparison())
                while self.at_operator(","):
                    self.take()
                    args.append(self.comparison())
            self.expect(")")
            return Call(function=upper, args=tuple(args))
        try:
            first = CellRef.parse(upper)
        except Invalid:
            return Name(name=upper)
        if self.at_operator(":"):
            self.take()
            second_token = self.take()
            if second_token.kind != KIND_WORD:
                raise Unparseable(
                    f"a range needs a second corner at "
                    f"position {second_token.position}"
                )
            second = CellRef.parse(second_token.text.upper())
            return Range(
                ref=RangeRef(
                    top=min(first.row, second.row),
                    left=min(first.col, second.col),
                    bottom=max(first.row, second.row),
                    right=max(first.col, second.col),
                )
            )
        return Ref(ref=first)


def parse_formula(text: str) -> Node:
    body = text[1:] if text.startswith("=") else text
    return Parser(tokens=lex(body)).parse()
