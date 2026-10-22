"""Pomodoro timer: a focus period followed by a break."""

from reloj import config

IDLE, FOCUS, BREAK = "idle", "focus", "break"


class Pomodoro:
    def __init__(self, focus_seconds: float = config.POMODORO_FOCUS_SECONDS,
                 break_seconds: float = config.POMODORO_BREAK_SECONDS,
                 bell_seconds: float = config.POMODORO_BELL_SECONDS):
        self.focus_seconds = focus_seconds
        self.break_seconds = break_seconds
        self.bell_seconds = bell_seconds
        self._focus_end: float | None = None

    def toggle(self, uptime: float):
        """Start a focus period, or cancel the current one."""
        self._focus_end = None if self._focus_end is not None else uptime + self.focus_seconds

    def update(self, uptime: float):
        """Go back to idle once the break is over."""
        if self._focus_end is not None and uptime - self._focus_end > self.break_seconds:
            self._focus_end = None

    def phase(self, uptime: float) -> str:
        if self._focus_end is None:
            return IDLE
        return FOCUS if self._focus_end - uptime > 0 else BREAK

    def remaining(self, uptime: float) -> float:
        """Seconds left in the focus period."""
        return self._focus_end - uptime if self._focus_end is not None else self.focus_seconds

    def progress(self, uptime: float) -> float:
        return 1 - self.remaining(uptime) / self.focus_seconds

    def wants_bell(self, uptime: float) -> bool:
        """True during the first seconds after the focus period ends."""
        return self._focus_end is not None and 0 <= uptime - self._focus_end < self.bell_seconds
