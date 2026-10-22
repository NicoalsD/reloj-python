"""Analog clock written in raw Python: no modules, no libraries.

The clock is rendered as an animated SVG image (SMIL animations),
so it keeps ticking in any browser without HTML, CSS or JavaScript.
"""

OUTPUT_FILE = "reloj.svg"
PROC_STAT_PATH = "/proc/stat"
PROC_UPTIME_PATH = "/proc/uptime"
RTC_EPOCH_PATH = "/sys/class/rtc/rtc0/since_epoch"


# ---------------------------------------------------------------------------
# System time
# ---------------------------------------------------------------------------

def read_boot_time():
    """Return the boot moment as seconds since 1970-01-01 UTC."""
    with open(PROC_STAT_PATH) as stat:
        for line in stat:
            if line.startswith("btime"):
                return int(line.split()[1])
    raise OSError("btime not found in " + PROC_STAT_PATH)


def read_uptime():
    """Return the seconds elapsed since boot, with centisecond precision."""
    with open(PROC_UPTIME_PATH) as uptime:
        return float(uptime.read().split()[0])


def read_rtc_epoch():
    """Read the hardware clock; less precise and may be stored in local time."""
    with open(RTC_EPOCH_PATH) as rtc:
        return float(rtc.read().strip())


def read_epoch():
    """Return the current UTC time as fractional seconds since 1970."""
    try:
        return read_boot_time() + read_uptime()
    except (OSError, ValueError, IndexError):
        return read_rtc_epoch()


def main():
    print("Reloj en Python")
    print("Segundos desde 1970 (UTC):", read_epoch())


if __name__ == "__main__":
    main()
