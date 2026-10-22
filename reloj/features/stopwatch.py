"""Stopwatch that can be paused."""


class Stopwatch:
    """Keeps the time saved by earlier runs plus the run in progress."""

    def __init__(self):
        self._started_at: float | None = None
        self._saved = 0.0

    @property
    def is_running(self) -> bool:
        return self._started_at is not None

    def toggle(self, uptime: float):
        """Start, or pause keeping the elapsed time."""
        if self._started_at is None:
            self._started_at = uptime
        else:
            self._saved += uptime - self._started_at
            self._started_at = None

    def reset(self):
        self._started_at, self._saved = None, 0.0

    def elapsed(self, uptime: float) -> float:
        running = uptime - self._started_at if self._started_at is not None else 0.0
        return self._saved + running
