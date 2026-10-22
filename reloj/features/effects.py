"""Fun visual modes: reverse clock, spinning dial and rainbow colors."""

from reloj import config


class Effects:
    def __init__(self, spin_seconds: float = config.SPIN_SECONDS,
                 rainbow_period: float = config.RAINBOW_PERIOD_SECONDS):
        self.reverse = False
        self.rainbow = False
        self._spin_seconds = spin_seconds
        self._rainbow_period = rainbow_period
        self._spin_start: float | None = None

    @property
    def direction(self) -> int:
        """1 for a normal clock, -1 when it runs counterclockwise."""
        return -1 if self.reverse else 1

    def toggle_reverse(self):
        self.reverse = not self.reverse

    def toggle_rainbow(self):
        self.rainbow = not self.rainbow

    def spin(self, uptime: float):
        self._spin_start = uptime

    def spin_angle(self, uptime: float) -> float:
        """Rotation of the whole dial, eased in and out, while a spin is running."""
        if self._spin_start is None:
            return 0.0
        progress = (uptime - self._spin_start) / self._spin_seconds
        if not 0 <= progress < 1:
            return 0.0
        return 360.0 * progress * progress * (3 - 2 * progress)

    def rainbow_phase(self, uptime: float) -> float | None:
        """Hue offset in [0, 1) that keeps moving, or None when the mode is off."""
        return (uptime / self._rainbow_period) % 1.0 if self.rainbow else None
