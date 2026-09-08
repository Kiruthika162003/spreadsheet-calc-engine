"""Day-count conventions: the 30/360 rules that bond desks actually use.

Interest accrues by a day-count convention, and the
conventions disagree by design, so a module that computed
"the" number of days between two dates would be wrong for
every desk but one. This module implements the family
explicitly. DAYS360 pretends every month has thirty days and
every year three hundred sixty, the convention behind most
corporate bonds, and it has two flavors that differ only in
how they handle a day-of-month of thirty-one: the US method
has a specific end-of-month adjustment sequence, and the
European method simply caps any thirty-first at thirty. The
difference is small and matters exactly at month ends, which
is where coupon dates live, so both are provided and named
rather than one chosen. YEARFRAC then divides the day count
by the year length its basis dictates: actual/365, actual/
360, or 30/360, and the basis is a required argument rather
than a default, because a year fraction whose basis is
implicit is the input to an interest calculation nobody can
reproduce. The dates are calendar serials from this package's
own epoch, and a start after the end yields a negative
fraction rather than an absolute value, because the sign
carries the direction of accrual and discarding it would make
a reversed pair silently indistinguishable from a forward
one.
"""

from __future__ import annotations

from gridiron.dates import from_serial
from gridiron.errors import Invalid


def days360(
    start_serial: int,
    end_serial: int,
    european: bool = False,
) -> int:
    start = from_serial(start_serial)
    end = from_serial(end_serial)
    d1, d2 = start.day, end.day
    if european:
        d1 = min(d1, 30)
        d2 = min(d2, 30)
    else:
        if d1 == 31:
            d1 = 30
        if d2 == 31 and d1 == 30:
            d2 = 30
    return (
        (end.year - start.year) * 360
        + (end.month - start.month) * 30
        + (d2 - d1)
    )


def year_fraction(
    start_serial: int,
    end_serial: int,
    basis: str,
) -> float:
    key = basis.strip().lower()
    if key == "actual/365":
        return (end_serial - start_serial) / 365.0
    if key == "actual/360":
        return (end_serial - start_serial) / 360.0
    if key == "30/360":
        return days360(start_serial, end_serial) / 360.0
    if key == "30e/360":
        return (
            days360(start_serial, end_serial, european=True)
            / 360.0
        )
    raise Invalid(
        f"unknown day-count basis {basis!r}; a year "
        "fraction with an implicit basis is not "
        "reproducible. Use actual/365, actual/360, 30/360, "
        "or 30e/360"
    )
