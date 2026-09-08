"""Currency conversion: rates against a base, and the cross rate triangulated through it.

A currency table cannot store every pair, so it stores each
currency's rate against one base and derives the rest by
triangulation: to convert A to B, go A to base to B. The
honest version of this states its base and refuses to invent
a rate it was not given rather than guessing, because a made-
up cross rate on an illiquid pair is the number that loses
money. The base currency has a rate of exactly one by
definition, set that way rather than stored, so it cannot
drift. Converting to or from a currency with no rate in the
table is refused with the missing code named, not defaulted
to one, because treating an unknown currency as the base
silently converts at par and par is almost never right.
Rates must be positive, a zero or negative rate being a
data-entry error that would divide the world by zero or flip
a sign, and both are refused. The conversion is exact in the
sense that round-tripping A to B to A returns the original
amount to within floating-point dust, a law the tests check,
because a rate table that cannot invert itself is arbitrage
waiting to be booked. Cross rates are computed through the
base in one step rather than stored, so adding a currency
means adding one rate, not one rate per existing pair, which
is why the base-relative table is the shape everyone uses.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid


@dataclass
class RateTable:
    base: str
    rates: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.base = self.base.upper()
        self.rates = {
            code.upper(): rate
            for code, rate in self.rates.items()
        }
        self.rates[self.base] = 1.0

    def set_rate(self, code: str, rate: float) -> None:
        if rate <= 0:
            raise Invalid(
                f"a rate of {rate} for {code} is a data "
                "error; rates are positive"
            )
        if code.upper() == self.base:
            raise Invalid(
                "the base currency's rate is one by "
                "definition and cannot be reset"
            )
        self.rates[code.upper()] = rate

    def _rate_of(self, code: str) -> float:
        key = code.upper()
        if key not in self.rates:
            raise Invalid(
                f"no rate for {code}; converting an unknown "
                "currency at par is almost never right"
            )
        return self.rates[key]

    def convert(
        self, amount: float, source: str, target: str
    ) -> float:
        source_rate = self._rate_of(source)
        target_rate = self._rate_of(target)
        # amount in source -> base -> target.
        in_base = amount / source_rate
        return in_base * target_rate

    def cross_rate(
        self, source: str, target: str
    ) -> float:
        return self.convert(1.0, source, target)
