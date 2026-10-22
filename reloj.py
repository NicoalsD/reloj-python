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


# ---------------------------------------------------------------------------
# Calendar math (Howard Hinnant's days <-> civil date algorithms)
# ---------------------------------------------------------------------------

SECONDS_PER_DAY = 86400


def days_from_civil(year, month, day):
    """Return the number of days between 1970-01-01 and the given date."""
    if month <= 2:
        year -= 1
    era = year // 400
    year_of_era = year - era * 400
    shifted_month = month - 3 if month > 2 else month + 9
    day_of_year = (153 * shifted_month + 2) // 5 + day - 1
    day_of_era = year_of_era * 365 + year_of_era // 4 - year_of_era // 100 + day_of_year
    return era * 146097 + day_of_era - 719468


def civil_from_days(days):
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


def weekday_from_days(days):
    """Return the weekday of a day count, 0 = Sunday."""
    return (days + 4) % 7


def days_in_month(year, month):
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    return days_from_civil(next_year, next_month, 1) - days_from_civil(year, month, 1)


def main():
    print("Reloj en Python")
    epoch = read_epoch()
    print("Fecha UTC:", civil_from_days(int(epoch // SECONDS_PER_DAY)))


if __name__ == "__main__":
    main()
