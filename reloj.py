"""Analog clock written in raw Python: no modules, no libraries.

The clock is rendered as an animated SVG image (SMIL animations),
so it keeps ticking in any browser without HTML, CSS or JavaScript.
"""

OUTPUT_FILE = "reloj.svg"
PROC_STAT_PATH = "/proc/stat"
PROC_UPTIME_PATH = "/proc/uptime"
RTC_EPOCH_PATH = "/sys/class/rtc/rtc0/since_epoch"
LOCAL_ZONE_PATH = "/etc/localtime"
ZONEINFO_DIR = "/usr/share/zoneinfo/"


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


DAY_NAMES = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]
MONTH_NAMES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
               "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def local_datetime(epoch, utc_offset):
    """Split an epoch into calendar fields for a given UTC offset in seconds."""
    local = epoch + utc_offset
    days = int(local // SECONDS_PER_DAY)
    seconds_of_day = local - days * SECONDS_PER_DAY
    year, month, day = civil_from_days(days)
    whole = int(seconds_of_day)
    return {
        "year": year,
        "month": month,
        "day": day,
        "days": days,
        "weekday": weekday_from_days(days),
        "hour": whole // 3600,
        "minute": whole // 60 % 60,
        "second": whole % 60,
        "seconds_of_day": seconds_of_day,
    }


def format_date(moment):
    """Return a Spanish long date such as 'martes, 21 de octubre de 2026'."""
    return "{}, {} de {} de {}".format(DAY_NAMES[moment["weekday"]], moment["day"],
                                      MONTH_NAMES[moment["month"] - 1], moment["year"])


def format_time(moment):
    return "{:02d}:{:02d}:{:02d}".format(moment["hour"], moment["minute"], moment["second"])


# ---------------------------------------------------------------------------
# Time zones: hand made reader for the binary TZif format (RFC 8536)
# ---------------------------------------------------------------------------

def read_int(data, start, size, signed=True):
    return int.from_bytes(data[start:start + size], "big", signed=signed)


def parse_tzif(path):
    """Read a zoneinfo file and return its transitions, types and footer rule."""
    with open(path, "rb") as source:
        data = source.read()
    if data[:4] != b"TZif":
        raise ValueError(path + " is not a TZif file")

    def block_sizes(header, time_size):
        counts = [read_int(data, header + 20 + 4 * index, 4, False) for index in range(6)]
        utc_count, std_count, leap_count, time_count, type_count, char_count = counts
        length = (time_count * time_size + time_count + type_count * 6 + char_count
                  + leap_count * (time_size + 4) + std_count + utc_count)
        return time_count, type_count, char_count, length

    header, time_size = 0, 4
    if data[4:5] >= b"2":
        # Skip the legacy 32-bit block and read the 64-bit one.
        header = 44 + block_sizes(0, 4)[3]
        time_size = 8
    time_count, type_count, char_count, length = block_sizes(header, time_size)

    cursor = header + 44
    transitions = [read_int(data, cursor + time_size * index, time_size)
                   for index in range(time_count)]
    cursor += time_size * time_count
    type_indexes = list(data[cursor:cursor + time_count])
    cursor += time_count
    types = []
    for index in range(type_count):
        start = cursor + 6 * index
        types.append((read_int(data, start, 4), data[start + 4], data[start + 5]))
    cursor += 6 * type_count
    names = data[cursor:cursor + char_count]

    def abbreviation(start):
        return names[start:names.index(b"\0", start)].decode("ascii")

    footer = ""
    if time_size == 8:
        footer = data[header + 44 + length:].strip(b"\n").decode("ascii")
    return {
        "transitions": transitions,
        "type_indexes": type_indexes,
        "types": [(offset, bool(dst), abbreviation(start)) for offset, dst, start in types],
        "footer": footer,
    }


def read_zone_name(spec, cursor):
    """Read a POSIX TZ abbreviation, either alphabetic or quoted with <>."""
    if spec[cursor] == "<":
        end = spec.index(">", cursor)
        return spec[cursor + 1:end], end + 1
    end = cursor
    while end < len(spec) and spec[end].isalpha():
        end += 1
    return spec[cursor:end], end


def read_clock_value(spec, cursor):
    """Read [+-]hh[:mm[:ss]] and return it in seconds."""
    sign = 1
    if cursor < len(spec) and spec[cursor] in "+-":
        sign = -1 if spec[cursor] == "-" else 1
        cursor += 1
    end = cursor
    while end < len(spec) and (spec[end].isdigit() or spec[end] == ":"):
        end += 1
    seconds = 0
    for part, scale in zip(spec[cursor:end].split(":"), (3600, 60, 1)):
        seconds += int(part) * scale
    return sign * seconds, end


def parse_rule_date(text):
    """Parse 'Mm.w.d[/time]' into (month, week, weekday, seconds)."""
    if not text.startswith("M"):
        return None
    date, _, moment = text[1:].partition("/")
    month, week, weekday = (int(part) for part in date.split("."))
    seconds = read_clock_value(moment, 0)[0] if moment else 7200
    return month, week, weekday, seconds


def parse_posix_rule(spec):
    """Parse a POSIX TZ string such as 'CET-1CEST,M3.5.0,M10.5.0/3'."""
    std_name, cursor = read_zone_name(spec, 0)
    std_west, cursor = read_clock_value(spec, cursor)
    rule = {"std": (-std_west, False, std_name), "dst": None}
    if cursor >= len(spec):
        return rule
    dst_name, cursor = read_zone_name(spec, cursor)
    dst_west = std_west - 3600
    if cursor < len(spec) and spec[cursor] != ",":
        dst_west, cursor = read_clock_value(spec, cursor)
    start, end = spec[cursor + 1:].split(",")
    start, end = parse_rule_date(start), parse_rule_date(end)
    if start and end:
        rule["dst"] = (-dst_west, True, dst_name)
        rule["start"], rule["end"] = start, end
    return rule


def rule_moment(year, rule_date):
    """Seconds since 1970 (in local wall time) for a 'Mm.w.d/time' rule."""
    month, week, weekday, seconds = rule_date
    first = days_from_civil(year, month, 1)
    day = 1 + (weekday - weekday_from_days(first)) % 7 + (week - 1) * 7
    while day > days_in_month(year, month):
        day -= 7
    return (first + day - 1) * SECONDS_PER_DAY + seconds


def posix_offset(rule, epoch):
    """Return the (offset, is_dst, name) a POSIX rule gives at an epoch."""
    std, dst = rule["std"], rule["dst"]
    if dst is None:
        return std
    year = civil_from_days(int((epoch + std[0]) // SECONDS_PER_DAY))[0]
    start = rule_moment(year, rule["start"]) - std[0]
    end = rule_moment(year, rule["end"]) - dst[0]
    if start < end:
        in_dst = start <= epoch < end
    else:
        in_dst = not end <= epoch < start
    return dst if in_dst else std


def zone_offset(zone, epoch):
    """Return the (offset, is_dst, name) of a parsed zone at an epoch."""
    transitions = zone["transitions"]
    if zone["footer"] and (not transitions or epoch >= transitions[-1]):
        return posix_offset(parse_posix_rule(zone["footer"]), epoch)
    current = None
    for index, moment in enumerate(transitions):
        if moment > epoch:
            break
        current = zone["type_indexes"][index]
    if current is None:
        standard = [kind for kind in zone["types"] if not kind[1]]
        return standard[0] if standard else zone["types"][0]
    return zone["types"][current]


def load_zone(name):
    """Load a zone by name (e.g. 'Asia/Tokyo'); None means the system zone."""
    return parse_tzif(LOCAL_ZONE_PATH if name is None else ZONEINFO_DIR + name)


def main():
    print("Reloj en Python")
    epoch = read_epoch()
    offset, _, zone_name = zone_offset(load_zone(None), epoch)
    now = local_datetime(epoch, offset)
    print("Hora local ({}):".format(zone_name), format_date(now), format_time(now))


if __name__ == "__main__":
    main()
