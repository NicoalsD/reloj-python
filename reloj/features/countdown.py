"""Countdown to a special day of the year."""

from reloj import config
from reloj.core.dates import SECONDS_PER_DAY, LocalTime, days_from_civil, days_in_month


class Countdown:
    def __init__(self, day: int = config.DEFAULT_COUNTDOWN[0],
                 month: int = config.DEFAULT_COUNTDOWN[1]):
        self.day, self.month = day, month

    def is_today(self, local: LocalTime) -> bool:
        return local.is_day(self.day, self.month)

    def target_epoch(self, local: LocalTime) -> float:
        """Local midnight of the next time the day comes (skipping years without 29/02)."""
        upcoming = (self.month, self.day) >= (local.month, local.day)
        year = local.year if upcoming else local.year + 1
        while days_in_month(year, self.month) < self.day:
            year += 1
        return days_from_civil(year, self.month, self.day) * SECONDS_PER_DAY - local.utc_offset

    def seconds_left(self, local: LocalTime) -> int:
        return int(self.target_epoch(local) - local.epoch)
