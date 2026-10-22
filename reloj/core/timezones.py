"""Time zones read from the binary TZif files (RFC 8536) without any library."""

from reloj import config
from reloj.core.dates import (SECONDS_PER_DAY, civil_from_days, days_from_civil,
                              days_in_month, weekday_from_days)


class ZoneState:
    """What a zone looks like at one instant: UTC offset, DST flag and abbreviation."""

    __slots__ = ("offset", "is_dst", "name")

    def __init__(self, offset: int, is_dst: bool, name: str):
        self.offset, self.is_dst, self.name = offset, is_dst, name

    def __repr__(self):
        return "ZoneState({}, {}, {!r})".format(self.offset, self.is_dst, self.name)


class PosixRule:
    """Footer rule such as 'CET-1CEST,M3.5.0,M10.5.0/3' used after the last transition."""

    def __init__(self, spec: str):
        std_name, cursor = _read_zone_name(spec, 0)
        std_west, cursor = _read_clock_value(spec, cursor)
        self.standard = ZoneState(-std_west, False, std_name)
        self.daylight = None
        self.start = self.end = None
        if cursor >= len(spec):
            return
        dst_name, cursor = _read_zone_name(spec, cursor)
        dst_west = std_west - 3600
        if cursor < len(spec) and spec[cursor] != ",":
            dst_west, cursor = _read_clock_value(spec, cursor)
        start, end = (_parse_rule_date(text) for text in spec[cursor + 1:].split(","))
        if start and end:
            self.daylight = ZoneState(-dst_west, True, dst_name)
            self.start, self.end = start, end

    def state_at(self, epoch: float) -> ZoneState:
        if self.daylight is None:
            return self.standard
        year = civil_from_days(int((epoch + self.standard.offset) // SECONDS_PER_DAY))[0]
        start = _rule_moment(year, self.start) - self.standard.offset
        end = _rule_moment(year, self.end) - self.daylight.offset
        if start < end:
            in_dst = start <= epoch < end
        else:   # southern hemisphere: DST spans the new year
            in_dst = not end <= epoch < start
        return self.daylight if in_dst else self.standard


class TimeZone:
    """A zone loaded from a zoneinfo file."""

    def __init__(self, transitions: list[int], type_indexes: list[int],
                 states: list[ZoneState], footer: str):
        self.transitions = transitions
        self.type_indexes = type_indexes
        self.states = states
        self.rule = PosixRule(footer) if footer else None

    @classmethod
    def local(cls) -> "TimeZone":
        return cls.from_file(config.LOCAL_ZONE_PATH)

    @classmethod
    def named(cls, name: str) -> "TimeZone":
        """Load a zone by name, for example 'Asia/Tokyo'."""
        return cls.from_file(config.ZONEINFO_DIR + name)

    @classmethod
    def from_file(cls, path: str) -> "TimeZone":
        with open(path, "rb") as source:
            return cls.from_bytes(source.read())

    @classmethod
    def from_bytes(cls, data: bytes) -> "TimeZone":
        if data[:4] != b"TZif":
            raise ValueError("not a TZif file")
        header, time_size = 0, 4
        if data[4:5] >= b"2":
            # Skip the legacy 32-bit block and read the 64-bit one.
            header = 44 + _block_sizes(data, 0, 4)[3]
            time_size = 8
        time_count, type_count, char_count, length = _block_sizes(data, header, time_size)

        cursor = header + 44
        transitions = [_read_int(data, cursor + time_size * index, time_size)
                       for index in range(time_count)]
        cursor += time_size * time_count
        type_indexes = list(data[cursor:cursor + time_count])
        cursor += time_count
        raw_types = []
        for index in range(type_count):
            start = cursor + 6 * index
            raw_types.append((_read_int(data, start, 4), data[start + 4], data[start + 5]))
        cursor += 6 * type_count
        names = data[cursor:cursor + char_count]
        states = [ZoneState(offset, bool(dst), names[start:names.index(b"\0", start)].decode())
                  for offset, dst, start in raw_types]

        footer = ""
        if time_size == 8:
            footer = data[header + 44 + length:].strip(b"\n").decode("ascii")
        return cls(transitions, type_indexes, states, footer)

    def state_at(self, epoch: float) -> ZoneState:
        if self.rule and (not self.transitions or epoch >= self.transitions[-1]):
            return self.rule.state_at(epoch)
        current = None
        for index, moment in enumerate(self.transitions):
            if moment > epoch:
                break
            current = self.type_indexes[index]
        if current is None:
            standard = [state for state in self.states if not state.is_dst]
            return standard[0] if standard else self.states[0]
        return self.states[current]

    def offset_at(self, epoch: float) -> int:
        return self.state_at(epoch).offset


def _read_int(data: bytes, start: int, size: int, signed: bool = True) -> int:
    return int.from_bytes(data[start:start + size], "big", signed=signed)


def _block_sizes(data: bytes, header: int, time_size: int) -> tuple[int, int, int, int]:
    """Counts from a TZif header and the byte length of the block that follows it."""
    counts = [_read_int(data, header + 20 + 4 * index, 4, False) for index in range(6)]
    utc_count, std_count, leap_count, time_count, type_count, char_count = counts
    length = (time_count * time_size + time_count + type_count * 6 + char_count
              + leap_count * (time_size + 4) + std_count + utc_count)
    return time_count, type_count, char_count, length


def _read_zone_name(spec: str, cursor: int) -> tuple[str, int]:
    """Read a POSIX TZ abbreviation, either alphabetic or quoted with <>."""
    if spec[cursor] == "<":
        end = spec.index(">", cursor)
        return spec[cursor + 1:end], end + 1
    end = cursor
    while end < len(spec) and spec[end].isalpha():
        end += 1
    return spec[cursor:end], end


def _read_clock_value(spec: str, cursor: int) -> tuple[int, int]:
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


def _parse_rule_date(text: str) -> tuple[int, int, int, int] | None:
    """Parse 'Mm.w.d[/time]' into (month, week, weekday, seconds)."""
    if not text.startswith("M"):
        return None
    date, _, moment = text[1:].partition("/")
    month, week, weekday = (int(part) for part in date.split("."))
    seconds = _read_clock_value(moment, 0)[0] if moment else 7200
    return month, week, weekday, seconds


def _rule_moment(year: int, rule_date: tuple[int, int, int, int]) -> int:
    """Seconds since 1970 (in local wall time) for a 'Mm.w.d/time' rule."""
    month, week, weekday, seconds = rule_date
    first = days_from_civil(year, month, 1)
    day = 1 + (weekday - weekday_from_days(first)) % 7 + (week - 1) * 7
    while day > days_in_month(year, month):
        day -= 7
    return (first + day - 1) * SECONDS_PER_DAY + seconds
