"""Daily alarm."""

from reloj import config
from reloj.core.dates import SECONDS_PER_DAY, LocalTime


class Alarm:
    """Rings for a while, once per day, when the chosen time arrives."""

    def __init__(self, ring_seconds: float = config.ALARM_RING_SECONDS):
        self.time: int | None = None          # seconds since midnight
        self._ring_seconds = ring_seconds
        self._rang_on_day: int | None = None
        self._ringing_until = 0.0

    def set(self, seconds_of_day: int | None):
        """Choose a new time, or None to remove the alarm."""
        self.time = seconds_of_day
        self._rang_on_day = None

    def update(self, local: LocalTime, uptime: float):
        """Start ringing during the alarm minute, unless it already rang today."""
        if self.time is None or self._rang_on_day == local.days:
            return
        if self.time <= local.seconds_of_day < self.time + 60:
            self._rang_on_day = local.days
            self._ringing_until = uptime + self._ring_seconds

    def is_ringing(self, uptime: float) -> bool:
        return self._ringing_until > uptime

    def silence(self):
        self._ringing_until = 0.0

    def seconds_left(self, local: LocalTime) -> float:
        return (self.time - local.seconds_of_day) % SECONDS_PER_DAY
