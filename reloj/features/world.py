"""Clocks for other cities."""

from reloj import config
from reloj.core.dates import LocalTime
from reloj.core.timezones import TimeZone


class WorldClock:
    """A city and its zone; the zone is None when its file could not be read."""

    def __init__(self, city: str, zone: TimeZone | None):
        self.city, self.zone = city, zone

    def local_time(self, epoch: float) -> LocalTime | None:
        if self.zone is None:
            return None
        return LocalTime(epoch, self.zone.offset_at(epoch))


def load_world_clocks(zones: list[tuple[str, str]] = config.WORLD_ZONES) -> list[WorldClock]:
    clocks = []
    for city, name in zones:
        try:
            zone = TimeZone.named(name)
        except (OSError, ValueError):
            zone = None
        clocks.append(WorldClock(city, zone))
    return clocks
