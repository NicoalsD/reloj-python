"""Every tool shown on the dashboard, kept together."""

from reloj.features.alarm import Alarm
from reloj.features.countdown import Countdown
from reloj.features.effects import Effects
from reloj.features.pomodoro import Pomodoro
from reloj.features.stopwatch import Stopwatch
from reloj.features.world import WorldClock


class Toolbox:
    def __init__(self, world: list[WorldClock]):
        self.world = world
        self.alarm = Alarm()
        self.stopwatch = Stopwatch()
        self.pomodoro = Pomodoro()
        self.countdown = Countdown()
        self.effects = Effects()

    def update(self, local, uptime: float):
        """Advance the tools that change on their own."""
        self.alarm.update(local, uptime)
        self.pomodoro.update(uptime)

    def wants_bell(self, uptime: float) -> bool:
        return self.alarm.is_ringing(uptime) or self.pomodoro.wants_bell(uptime)
