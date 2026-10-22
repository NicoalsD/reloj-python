"""Calendar math with Howard Hinnant's days <-> civil date algorithms."""

SECONDS_PER_DAY = 86400


def days_from_civil(year: int, month: int, day: int) -> int:
    """Return the number of days between 1970-01-01 and the given date."""
    if month <= 2:
        year -= 1
    era = year // 400
    year_of_era = year - era * 400
    shifted_month = month - 3 if month > 2 else month + 9
    day_of_year = (153 * shifted_month + 2) // 5 + day - 1
    day_of_era = year_of_era * 365 + year_of_era // 4 - year_of_era // 100 + day_of_year
    return era * 146097 + day_of_era - 719468


def civil_from_days(days: int) -> tuple[int, int, int]:
    """Return (year, month, day) for a count of days since 1970-01-01."""
    days += 719468
    era = days // 146097
    day_of_era = days - era * 146097
    year_of_era = (day_of_era - day_of_era // 1460 + day_of_era // 36524
                   - day_of_era // 146096) // 365
    day_of_year = day_of_era - (365 * year_of_era + year_of_era // 4 - year_of_era // 100)
    shifted_month = (5 * day_of_year + 2) // 153
    day = day_of_year - (153 * shifted_month + 2) // 5 + 1
    month = shifted_month + 3 if shifted_month < 10 else shifted_month - 9
    year = year_of_era + era * 400
    if month <= 2:
        year += 1
    return year, month, day


def weekday_from_days(days: int) -> int:
    """Return the weekday of a day count, 0 = Sunday."""
    return (days + 4) % 7


def days_in_month(year: int, month: int) -> int:
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    return days_from_civil(next_year, next_month, 1) - days_from_civil(year, month, 1)


class LocalTime:
    """Calendar fields of an instant seen from a UTC offset given in seconds."""

    __slots__ = ("epoch", "utc_offset", "days", "seconds_of_day", "year", "month", "day",
                 "weekday", "hour", "minute", "second")

    def __init__(self, epoch: float, utc_offset: int = 0):
        local = epoch + utc_offset
        self.epoch = epoch
        self.utc_offset = utc_offset
        self.days = int(local // SECONDS_PER_DAY)
        self.seconds_of_day = local - self.days * SECONDS_PER_DAY
        self.year, self.month, self.day = civil_from_days(self.days)
        self.weekday = weekday_from_days(self.days)
        whole = int(self.seconds_of_day)
        self.hour, self.minute, self.second = whole // 3600, whole // 60 % 60, whole % 60

    def is_day(self, day: int, month: int) -> bool:
        return (self.day, self.month) == (day, month)
