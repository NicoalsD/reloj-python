"""Current time read from Linux files instead of the time module."""

from reloj import config
from reloj.core.dates import LocalTime


class ClockReading:
    """One sample of the clock: seconds since boot, UTC epoch and local calendar fields."""

    __slots__ = ("uptime", "epoch", "local")

    def __init__(self, uptime: float, epoch: float, local: LocalTime):
        self.uptime, self.epoch, self.local = uptime, epoch, local


class SystemClock:
    """Wall clock built from the boot moment (/proc/stat) plus the uptime counter."""

    def __init__(self, uptime_path: str = config.PROC_UPTIME_PATH,
                 stat_path: str = config.PROC_STAT_PATH, rtc_path: str = config.RTC_EPOCH_PATH):
        self._uptime_path = uptime_path
        self.boot_epoch = self._read_boot_epoch(stat_path, rtc_path)

    def uptime(self) -> float:
        """Seconds since boot, with centisecond precision."""
        with open(self._uptime_path) as source:
            return float(source.read().split()[0])

    def read(self, zone) -> ClockReading:
        """Sample the clock; 'zone' is anything with an offset_at(epoch) method."""
        uptime = self.uptime()
        epoch = self.boot_epoch + uptime
        return ClockReading(uptime, epoch, LocalTime(epoch, zone.offset_at(epoch)))

    def wait_until(self, uptime_target: float):
        """There is no sleep() without the time module, so keep checking the counter."""
        while self.uptime() < uptime_target:
            pass

    def _read_boot_epoch(self, stat_path: str, rtc_path: str) -> float:
        try:
            with open(stat_path) as stat:
                for line in stat:
                    if line.startswith("btime"):
                        return float(line.split()[1])
            raise ValueError("btime not found in " + stat_path)
        except (OSError, ValueError, IndexError):
            # The hardware clock is less precise and may even be stored in local time.
            with open(rtc_path) as rtc:
                return float(rtc.read().strip()) - self.uptime()
