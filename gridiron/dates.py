"""Date serials: days since the epoch, with the famous bug refused.

Spreadsheet dates are numbers wearing a costume: day one is
the epoch and arithmetic on dates is arithmetic on floats,
which is why deadline minus today works in a cell. The
incumbent's serial system carries a deliberate ancient lie,
it believes 1900 was a leap year to stay compatible with the
software it displaced, and every clone since has had to
choose between the lie and the misalignment. This engine
chooses a clean epoch instead: day 1 is the first of January
2000, a real date in a real calendar, documented here so the
choice is a decision and not an accident, and conversion
helpers translate to and from calendar triples with the
Gregorian rules applied exactly. Serial zero and negatives
are refused, because a date before the epoch is a modeling
question the modeler should answer with a different column,
not a number the engine should quietly extrapolate.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid

_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
EPOCH_YEAR = 2000


def is_leap(year: int) -> bool:
    return year % 4 == 0 and (
        year % 100 != 0 or year % 400 == 0
    )


def days_in_month(year: int, month: int) -> int:
    if not 1 <= month <= 12:
        raise Invalid(f"month {month} is not on any calendar")
    if month == 2 and is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month - 1]


def days_in_year(year: int) -> int:
    return 366 if is_leap(year) else 365


@dataclass(frozen=True, order=True)
class CalendarDate:
    year: int
    month: int
    day: int

    def __post_init__(self) -> None:
        if self.year < EPOCH_YEAR:
            raise Invalid(
                f"{self.year} predates the epoch; a date "
                "before it is a modeling question, not a "
                "number to extrapolate"
            )
        if not 1 <= self.day <= days_in_month(
            self.year, self.month
        ):
            raise Invalid(
                f"{self.year}-{self.month:02}-{self.day:02} "
                "is not a date the Gregorian calendar contains"
            )


def to_serial(date: CalendarDate) -> int:
    total = 0
    for year in range(EPOCH_YEAR, date.year):
        total += days_in_year(year)
    for month in range(1, date.month):
        total += days_in_month(date.year, month)
    return total + date.day


def from_serial(serial: int) -> CalendarDate:
    if serial < 1:
        raise Invalid(
            f"serial {serial} predates the epoch; day 1 is "
            "2000-01-01 by documented decision, not accident"
        )
    remaining = serial
    year = EPOCH_YEAR
    while remaining > days_in_year(year):
        remaining -= days_in_year(year)
        year += 1
    month = 1
    while remaining > days_in_month(year, month):
        remaining -= days_in_month(year, month)
        month += 1
    return CalendarDate(year=year, month=month, day=remaining)


def weekday(serial: int) -> int:
    """1 is Monday through 7 is Sunday; 2000-01-01 was a Saturday."""
    return ((serial - 1) + 5) % 7 + 1


def render_date(serial: int) -> str:
    date = from_serial(serial)
    return f"{date.year}-{date.month:02}-{date.day:02}"
