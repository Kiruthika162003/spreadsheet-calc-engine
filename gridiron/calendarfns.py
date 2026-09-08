"""Calendar helpers: naming the parts of a date, and the ISO week that starts on Monday.

These are the small date questions a report asks constantly:
which quarter is this, what month is it named, how many days
does this month have, is this a leap year. They read from the
package's own calendar rather than the host system's, so a
sheet computes the same answer on any machine and in any
timezone, which is the whole reason this package refused an
ambient clock in the first place. QUARTER maps months one to
twelve onto one to four the obvious way. DAYS_IN_MONTH honors
the real leap-year rule, the one the date module already
enforces rather than the 1900 lie some spreadsheets still
carry, so February 2000 has twenty-nine days and February
1900, had it existed in this epoch, would not. The ISO week
number is the one that trips everyone: ISO weeks start on
Monday and week one is the week containing the year's first
Thursday, so early January can belong to the last week of the
previous year and late December to week one of the next, and
this computes it by the definition rather than a naive
day-of-year over seven that would put January first in week
one always and be wrong most years. Month and day names come
back full and are refused for an out-of-range index rather
than wrapping, because month thirteen is a bug in the caller,
not December of next year, and silently wrapping it hides the
off-by-one that produced it.
"""

from __future__ import annotations

from gridiron.dates import (
    CalendarDate,
    days_in_month,
    from_serial,
    to_serial,
    weekday,
)
from gridiron.errors import Invalid

_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November",
    "December",
)
_DAYS = (
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday", "Sunday",
)


def quarter(serial: int) -> int:
    month = from_serial(serial).month
    return (month - 1) // 3 + 1


def month_name(month: int) -> str:
    if not 1 <= month <= 12:
        raise Invalid(
            f"month {month} does not exist; thirteen is a "
            "caller bug, not December of next year"
        )
    return _MONTHS[month - 1]


def day_name(serial: int) -> str:
    return _DAYS[weekday(serial) - 1]


def days_in(year: int, month: int) -> int:
    if not 1 <= month <= 12:
        raise Invalid(f"month {month} does not exist")
    return days_in_month(year, month)


def is_leap_year(year: int) -> bool:
    return days_in_month(year, 2) == 29


def iso_week(serial: int) -> int:
    date = from_serial(serial)
    # The Thursday of this date's ISO week determines the
    # year the week belongs to; week one holds January's
    # first Thursday.
    iso_weekday = weekday(serial)
    thursday_serial = serial - (iso_weekday - 4)
    thursday = from_serial(thursday_serial)
    jan1 = to_serial(
        CalendarDate(year=thursday.year, month=1, day=1)
    )
    return (thursday_serial - jan1) // 7 + 1
