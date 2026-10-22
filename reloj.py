"""Analog clock written in raw Python: no modules, no libraries.

The clock is drawn in the terminal with Unicode braille dots, block digits
and ANSI colors, refreshed in place several times per second.
"""

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


def format_clock(seconds_of_day):
    return "{:02d}:{:02d}".format(int(seconds_of_day) // 3600, int(seconds_of_day) // 60 % 60)


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


# ---------------------------------------------------------------------------
# Trigonometry with Taylor series
# ---------------------------------------------------------------------------

PI = 3.141592653589793


def sin(angle):
    """Sine using its Taylor series after reducing the angle to [-pi, pi]."""
    angle = angle % (2 * PI)
    if angle > PI:
        angle -= 2 * PI
    term = total = angle
    for step in range(1, 12):
        term *= -angle * angle / ((2 * step) * (2 * step + 1))
        total += term
    return total


def cos(angle):
    return sin(angle + PI / 2)


def polar(center_x, center_y, radius, degrees):
    """Point on a clock dial: 0 degrees is 12 o'clock, growing clockwise."""
    radians = degrees * PI / 180
    return center_x + radius * sin(radians), center_y - radius * cos(radians)


# ---------------------------------------------------------------------------
# Braille canvas: every terminal cell holds a 2 x 4 grid of dots
# ---------------------------------------------------------------------------

BRAILLE_BASE = 0x2800
BRAILLE_BITS = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]


class Canvas:
    """Dot canvas; pixels are square because a cell is twice as tall as wide."""

    def __init__(self, columns, rows):
        self.columns, self.rows = columns, rows
        self.width, self.height = columns * 2, rows * 4
        self.bits = [[0] * columns for _ in range(rows)]
        self.colors = [[None] * columns for _ in range(rows)]
        self.labels = {}

    def dot(self, x, y, color):
        x, y = int(x + 0.5), int(y + 0.5)
        if 0 <= x < self.width and 0 <= y < self.height:
            row, column = y // 4, x // 2
            self.bits[row][column] |= BRAILLE_BITS[y % 4][x % 2]
            self.colors[row][column] = color

    def line(self, x1, y1, x2, y2, color, thickness=0.0):
        """Straight line; 'thickness' adds parallel lines on both sides."""
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 or 1.0
        normal_x, normal_y = -(y2 - y1) / length, (x2 - x1) / length
        steps = int(length * 2) + 1
        shift = -thickness
        while shift <= thickness:
            for step in range(steps + 1):
                ratio = step / steps
                self.dot(x1 + (x2 - x1) * ratio + normal_x * shift,
                         y1 + (y2 - y1) * ratio + normal_y * shift, color)
            shift += 0.5

    def circle(self, cx, cy, radius, color):
        steps = int(radius * 8) + 8
        for step in range(steps):
            self.dot(*polar(cx, cy, radius, 360.0 * step / steps), color=color)

    def label(self, x, y, content, color):
        """Plain text placed over the dots, centered on the pixel (x, y)."""
        row, column = int(y) // 4, int(x) // 2 - len(content) // 2
        for index, character in enumerate(content):
            self.labels[(row, column + index)] = (character, color)

    def cells(self):
        """Yield (row, column, character, color) for every cell."""
        for row in range(self.rows):
            for column in range(self.columns):
                if (row, column) in self.labels:
                    yield (row, column) + self.labels[(row, column)]
                elif self.bits[row][column]:
                    yield (row, column, chr(BRAILLE_BASE + self.bits[row][column]),
                           self.colors[row][column])
                else:
                    yield row, column, " ", None


# ---------------------------------------------------------------------------
# Analog clock drawing
# ---------------------------------------------------------------------------

def draw_dial(canvas, direction=1, turn=0.0):
    """Rim, minute dots, hour ticks and the numbers 1 to 12."""
    cx, cy = canvas.width / 2, canvas.height / 2
    radius = min(cx, cy) - 2
    canvas.circle(cx, cy, radius, "frame")
    canvas.circle(cx, cy, radius - 0.8, "frame")
    for tick in range(60):
        angle = tick * 6 * direction + turn
        if tick % 5 == 0:
            canvas.line(*(polar(cx, cy, radius * 0.86, angle) + polar(cx, cy, radius * 0.95, angle)),
                        color="ink", thickness=0.5)
        else:
            canvas.dot(*polar(cx, cy, radius * 0.94, angle), color="muted")
    for hour in range(1, 13):
        x, y = polar(cx, cy, radius * 0.72, hour * 30 * direction + turn)
        canvas.label(x, y, str(hour), "highlight" if hour % 3 == 0 else "ink")


def draw_hands(canvas, seconds_of_day, direction=1, turn=0.0):
    """Hour and minute hands move smoothly; the second hand jumps like a real one."""
    cx, cy = canvas.width / 2, canvas.height / 2
    radius = min(cx, cy) - 2
    hour = (seconds_of_day % 43200) / 120.0 * direction + turn
    minute = (seconds_of_day % 3600) / 10.0 * direction + turn
    second = int(seconds_of_day % 60) * 6 * direction + turn
    canvas.line(cx, cy, *polar(cx, cy, radius * 0.48, hour), color="ink", thickness=1.5)
    canvas.line(cx, cy, *polar(cx, cy, radius * 0.76, minute), color="ink", thickness=0.5)
    canvas.line(*(polar(cx, cy, radius * 0.18, second + 180) + polar(cx, cy, radius * 0.86, second)),
                color="accent")
    for ring in (0.5, 1.2, 2.0):
        canvas.circle(cx, cy, ring, "accent")


# ---------------------------------------------------------------------------
# Terminal screen with 24-bit ANSI colors
# ---------------------------------------------------------------------------

ESCAPE = "\x1b["
RESET = ESCAPE + "0m"
THEMES = [
    ("Medianoche", {"bg": (15, 17, 35), "ink": (226, 232, 255), "accent": (255, 94, 98),
                    "muted": (110, 118, 160), "highlight": (138, 180, 255),
                    "frame": (70, 80, 140)}),
    ("Clásico", {"bg": (244, 247, 251), "ink": (31, 42, 90), "accent": (232, 64, 42),
                 "muted": (138, 144, 166), "highlight": (142, 43, 143),
                 "frame": (31, 42, 90)}),
    ("Neón", {"bg": (13, 2, 33), "ink": (244, 241, 255), "accent": (255, 42, 109),
              "muted": (157, 143, 214), "highlight": (5, 217, 232), "frame": (255, 42, 109)}),
    ("Matrix", {"bg": (0, 0, 0), "ink": (57, 255, 20), "accent": (198, 255, 0),
                "muted": (31, 143, 58), "highlight": (0, 255, 156), "frame": (20, 110, 40)}),
    ("Atardecer", {"bg": (45, 20, 44), "ink": (255, 236, 214), "accent": (255, 107, 53),
                   "muted": (181, 131, 141), "highlight": (255, 183, 3),
                   "frame": (230, 57, 70)}),
]


def foreground(rgb):
    return ESCAPE + "38;2;{};{};{}m".format(*rgb)


def background(rgb):
    return ESCAPE + "48;2;{};{};{}m".format(*rgb)


class Screen:
    """Grid of characters; colors are palette role names or (r, g, b) tuples."""

    def __init__(self, width, height):
        self.width, self.height = width, height
        self.chars = [[" "] * width for _ in range(height)]
        self.colors = [[None] * width for _ in range(height)]

    def put(self, x, y, content, color=None):
        for index, character in enumerate(content):
            if 0 <= x + index < self.width and 0 <= y < self.height:
                self.chars[y][x + index] = character
                self.colors[y][x + index] = color

    def center(self, y, content, color=None, left=0, right=None):
        right = self.width if right is None else right
        self.put(left + (right - left - len(content)) // 2, y, content, color)

    def draw_canvas(self, canvas, x, y):
        for row, column, character, color in canvas.cells():
            self.put(x + column, y + row, character, color)

    def render(self, palette):
        """Return the whole frame, emitting a color code only when it changes."""
        lines = []
        for y in range(self.height):
            parts, current = [background(palette["bg"])], None
            for x in range(self.width):
                color = self.colors[y][x] or "ink"
                rgb = palette[color] if isinstance(color, str) else color
                if rgb != current:
                    parts.append(foreground(rgb))
                    current = rgb
                parts.append(self.chars[y][x])
            lines.append("".join(parts) + RESET)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Big block digits
# ---------------------------------------------------------------------------

BIG_FONT = {
    "0": ["█████", "█   █", "█   █", "█   █", "█████"],
    "1": ["  █  ", " ██  ", "  █  ", "  █  ", " ███ "],
    "2": ["█████", "    █", "█████", "█    ", "█████"],
    "3": ["█████", "    █", " ████", "    █", "█████"],
    "4": ["█   █", "█   █", "█████", "    █", "    █"],
    "5": ["█████", "█    ", "█████", "    █", "█████"],
    "6": ["█████", "█    ", "█████", "█   █", "█████"],
    "7": ["█████", "    █", "   █ ", "  █  ", "  █  "],
    "8": ["█████", "█   █", "█████", "█   █", "█████"],
    "9": ["█████", "█   █", "█████", "    █", "█████"],
    ":": ["   ", " ▀ ", "   ", " ▀ ", "   "],
    " ": ["   ", "   ", "   ", "   ", "   "],
}


def big_text(content):
    """Return the five rows of 'content' written with BIG_FONT."""
    return [" ".join(BIG_FONT[character][row] for character in content) for row in range(5)]


def big_width(content):
    return len(big_text(content)[0])


# ---------------------------------------------------------------------------
# Spanish texts
# ---------------------------------------------------------------------------

def greeting(hour):
    if hour < 6:
        return "¡A dormir, búho nocturno!"
    if hour < 12:
        return "¡Buenos días!"
    if hour < 14:
        return "¡Hora de almorzar!"
    if hour < 19:
        return "¡Buenas tardes!"
    return "¡Buenas noches!"


WORLD_ZONES = [
    ("Bogotá", "America/Bogota"),
    ("Madrid", "Europe/Madrid"),
    ("Tokio", "Asia/Tokyo"),
    ("Nueva York", "America/New_York"),
]


def format_utc_offset(offset):
    sign = "+" if offset >= 0 else "-"
    hours, minutes = abs(offset) // 3600, abs(offset) // 60 % 60
    return "UTC{}{}{}".format(sign, hours, ":{:02d}".format(minutes) if minutes else "")


def relative_day(days, home_days):
    return {-1: "ayer", 0: "hoy", 1: "mañana"}.get(days - home_days, "")


HOUR_WORDS = ["doce", "una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
              "nueve", "diez", "once"]
NUMBER_WORDS = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
                "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete",
                "dieciocho", "diecinueve", "veinte", "veintiuno", "veintidós", "veintitrés",
                "veinticuatro", "veinticinco", "veintiséis", "veintisiete", "veintiocho",
                "veintinueve"]


def time_in_words(hour, minute):
    """Spanish spoken time: 'Son las tres y cuarto', 'Es la una menos diez'."""
    if minute <= 30:
        target = hour % 12
        special = {0: "en punto", 15: "y cuarto", 30: "y media"}
        tail = special[minute] if minute in special else "y " + NUMBER_WORDS[minute]
    else:
        target = (hour + 1) % 12
        tail = "menos cuarto" if minute == 45 else "menos " + NUMBER_WORDS[60 - minute]
    start = "Es la una" if target == 1 else "Son las " + HOUR_WORDS[target]
    return start + " " + tail


# ---------------------------------------------------------------------------
# Frame layout
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 100, 27
CLOCK_COLUMNS, CLOCK_ROWS = 46, 23
PANEL_LEFT, PANEL_RIGHT = 52, 97


def mix(first, second, ratio):
    """Blend two RGB colors."""
    return tuple(int(a + (b - a) * ratio) for a, b in zip(first, second))


def draw_border(screen, title, footer):
    screen.put(0, 0, "╭" + "─" * (WIDTH - 2) + "╮", "frame")
    for y in range(1, HEIGHT - 1):
        screen.put(0, y, "│", "frame")
        screen.put(WIDTH - 1, y, "│", "frame")
    screen.put(0, HEIGHT - 1, "╰" + "─" * (WIDTH - 2) + "╯", "frame")
    screen.put(3, 0, " " + title + " ", "highlight")
    screen.put(3, HEIGHT - 1, " " + footer + " ", "muted")


def draw_big_time(screen, y, content, palette):
    """Block digits with a vertical gradient from 'highlight' to 'accent'."""
    rows = big_text(content)
    x = PANEL_LEFT + (PANEL_RIGHT - PANEL_LEFT - len(rows[0])) // 2
    for index, row in enumerate(rows):
        screen.put(x, y + index, row, mix(palette["highlight"], palette["accent"], index / 4))


def section_title(screen, y, title):
    line = "─" * ((PANEL_RIGHT - PANEL_LEFT - len(title) - 2) // 2)
    screen.center(y, "{} {} {}".format(line, title, line), "frame", PANEL_LEFT, PANEL_RIGHT)


QUARTER_SYMBOLS = "◴◷◶◵"


def draw_world(screen, y, state):
    section_title(screen, y, "Relojes del mundo")
    for index, (city, zone) in enumerate(state["world"]):
        row = y + 1 + index
        if zone is None:
            screen.put(PANEL_LEFT + 2, row, city + ": zona no disponible", "muted")
            continue
        offset = zone_offset(zone, state["epoch"])[0]
        moment = local_datetime(state["epoch"], offset)
        screen.put(PANEL_LEFT + 2, row, QUARTER_SYMBOLS[moment["minute"] // 15], "accent")
        screen.put(PANEL_LEFT + 4, row, city, "ink")
        screen.put(PANEL_LEFT + 17, row, format_time(moment), "highlight")
        screen.put(PANEL_LEFT + 28, row, format_utc_offset(offset), "muted")
        screen.put(PANEL_LEFT + 37, row, relative_day(moment["days"], state["now"]["days"]),
                   "muted")


def load_world():
    """Parse every world zone once; a missing file just shows a notice."""
    world = []
    for city, name in WORLD_ZONES:
        try:
            world.append((city, load_zone(name)))
        except (OSError, ValueError):
            world.append((city, None))
    return world


def format_duration(seconds):
    seconds = int(seconds)
    hours, minutes = seconds // 3600, seconds // 60 % 60
    if hours:
        return "{} h {:02d} min".format(hours, minutes)
    return "{} min {:02d} s".format(minutes, seconds % 60)


def draw_tool(screen, y, name, value, detail="", value_color="highlight"):
    screen.put(PANEL_LEFT + 2, y, name, "muted")
    screen.put(PANEL_LEFT + 15, y, value, value_color)
    screen.put(PANEL_LEFT + 15 + len(value) + 2, y, detail, "muted")


def draw_alarm(screen, y, state):
    alarm = state["alarm"]
    if alarm is None:
        draw_tool(screen, y, "Alarma", "--:--", "sin programar", "muted")
        return
    if is_ringing(state):
        draw_tool(screen, y, "Alarma", format_clock(alarm), "¡sonando!", "accent")
        return
    left = (alarm - state["now"]["seconds_of_day"]) % SECONDS_PER_DAY
    draw_tool(screen, y, "Alarma", format_clock(alarm), "faltan " + format_duration(left))


def update_alarm(state):
    """Start ringing for one minute when the alarm time arrives (once per day)."""
    alarm, now = state["alarm"], state["now"]
    if alarm is None or state["alarm_day"] == now["days"]:
        return
    if alarm <= now["seconds_of_day"] < alarm + 60:
        state["alarm_day"] = now["days"]
        state["ringing_until"] = state["uptime"] + 60


def is_ringing(state):
    return state["ringing_until"] > state["uptime"]


def draw_alarm_banner(screen, state):
    message = " ¡ALARMA! Son las {} · Ctrl+C para apagarla ".format(format_clock(state["alarm"]))
    flash = int(state["uptime"] * 2) % 2 == 0
    screen.center(HEIGHT - 2, message, "accent" if flash else "highlight")


def stopwatch_elapsed(state):
    running = state["uptime"] - state["sw_started"] if state["sw_started"] is not None else 0.0
    return state["sw_saved"] + running


def draw_stopwatch(screen, y, state):
    elapsed = stopwatch_elapsed(state)
    value = "{:02d}:{:02d}.{}".format(int(elapsed) // 60, int(elapsed) % 60, int(elapsed * 10) % 10)
    if state["sw_started"] is not None:
        draw_tool(screen, y, "Cronómetro", value, "en marcha", "accent")
    elif elapsed:
        draw_tool(screen, y, "Cronómetro", value, "en pausa")
    else:
        draw_tool(screen, y, "Cronómetro", value, "detenido", "muted")


POMODORO_SECONDS = 25 * 60
BAR_PARTS = " ▏▎▍▌▋▊▉█"


def progress_bar(ratio, width):
    """Smooth bar using the eighth-width block characters."""
    eighths = int(max(0.0, min(1.0, ratio)) * width * 8)
    bar = "█" * (eighths // 8)
    if len(bar) < width:
        bar += BAR_PARTS[eighths % 8]
    return bar + " " * (width - len(bar))


def draw_pomodoro(screen, y, state):
    end = state["pomo_end"]
    if end is None:
        draw_tool(screen, y, "Pomodoro", "25:00", "listo para enfocarte", "muted")
        return
    left = end - state["uptime"]
    if left <= 0:
        draw_tool(screen, y, "Pomodoro", "00:00", "¡Descansa 5 minutos!", "accent")
        return
    bar = progress_bar(1 - left / POMODORO_SECONDS, 18)
    screen.put(PANEL_LEFT + 2, y, "Pomodoro", "muted")
    screen.put(PANEL_LEFT + 15, y, "{:02d}:{:02d}".format(int(left) // 60, int(left) % 60),
               "highlight")
    screen.put(PANEL_LEFT + 22, y, "▕" + bar + "▏", "accent")


def countdown_target(state):
    """Local midnight of the next occurrence of the chosen day and month."""
    day, month = state["countdown"]
    now = state["now"]
    year = now["year"] + (1 if (month, day) < (now["month"], now["day"]) else 0)
    while days_in_month(year, month) < day:
        year += 1
    return days_from_civil(year, month, day) * SECONDS_PER_DAY - state["offset"]


def draw_countdown(screen, y, state):
    day, month = state["countdown"]
    title = "{} de {}".format(day, MONTH_NAMES[month - 1])
    if (month, day) == (state["now"]["month"], state["now"]["day"]):
        draw_tool(screen, y, "Cuenta atrás", "¡Hoy es el día!", title, "accent")
        return
    left = int(countdown_target(state) - state["epoch"])
    value = "{}d {:02d}:{:02d}:{:02d}".format(left // SECONDS_PER_DAY, left // 3600 % 24,
                                             left // 60 % 60, left % 60)
    draw_tool(screen, y, "Cuenta atrás", value, title)


SPIN_SECONDS = 1.5


def spin_angle(state):
    """Whole-dial rotation for the '¡Girar!' trick, eased in and out."""
    progress = (state["uptime"] - state["spin_start"]) / SPIN_SECONDS
    if not 0 <= progress < 1:
        return 0.0
    eased = progress * progress * (3 - 2 * progress)
    return 360.0 * eased


def build_frame(state):
    palette = THEMES[state["theme"]][1]
    now = state["now"]
    screen = Screen(WIDTH, HEIGHT)
    draw_border(screen, "Reloj en Python", "Ctrl+C: menú · Python puro, cero librerías")
    canvas = Canvas(CLOCK_COLUMNS, CLOCK_ROWS)
    direction = -1 if state["reverse"] else 1
    turn = spin_angle(state)
    draw_dial(canvas, direction, turn)
    draw_hands(canvas, now["seconds_of_day"], direction, turn)
    if state["reverse"]:
        screen.center(HEIGHT - 2, "~ modo al revés ~", "muted", 3, 3 + CLOCK_COLUMNS)
    screen.draw_canvas(canvas, 3, 2)
    draw_big_time(screen, 3, format_time(now), palette)
    date = format_date(now)
    screen.center(9, date[0].upper() + date[1:], "muted", PANEL_LEFT, PANEL_RIGHT)
    screen.center(10, "~ " + greeting(now["hour"]) + " ~", "highlight", PANEL_LEFT, PANEL_RIGHT)
    screen.center(11, "« " + time_in_words(now["hour"], now["minute"]) + " »", "ink",
                  PANEL_LEFT, PANEL_RIGHT)
    draw_world(screen, 13, state)
    section_title(screen, 19, "Herramientas")
    draw_alarm(screen, 20, state)
    draw_stopwatch(screen, 21, state)
    draw_pomodoro(screen, 22, state)
    draw_countdown(screen, 23, state)
    if is_ringing(state):
        draw_alarm_banner(screen, state)
    return screen


# ---------------------------------------------------------------------------
# Live loop
# ---------------------------------------------------------------------------

FRAME_SECONDS = 0.1
ENTER_SCREEN = ESCAPE + "?1049h" + ESCAPE + "?25l"   # alternate screen, hide cursor
LEAVE_SCREEN = ESCAPE + "?25h" + ESCAPE + "?1049l"
HOME = ESCAPE + "H"


def wait_until(uptime_target):
    """There is no sleep() without modules, so keep checking the uptime counter."""
    while read_uptime() < uptime_target:
        pass


def update_time(state):
    uptime = read_uptime()
    state["uptime"] = uptime
    state["epoch"] = state["boot"] + uptime
    state["offset"] = zone_offset(state["zone"], state["epoch"])[0]
    state["now"] = local_datetime(state["epoch"], state["offset"])


def run_clock(state):
    """Redraw in place until Ctrl+C."""
    print(ENTER_SCREEN, end="")
    try:
        next_frame = read_uptime()
        while True:
            update_time(state)
            update_alarm(state)
            palette = THEMES[state["theme"]][1]
            bell = ""
            pomo_end = state["pomo_end"]
            if pomo_end is not None and 0 <= state["uptime"] - pomo_end < 3:
                if int(state["uptime"]) != state["last_bell"]:
                    state["last_bell"] = int(state["uptime"])
                    bell = "\a"
            if pomo_end is not None and state["uptime"] - pomo_end > 300:
                state["pomo_end"] = None   # the break is over
            if is_ringing(state):
                palette = dict(palette)
                if int(state["uptime"] * 2) % 2 == 0:
                    palette["frame"] = palette["accent"]
                if int(state["uptime"]) != state["last_bell"]:
                    state["last_bell"] = int(state["uptime"])
                    bell = "\a"
            frame = build_frame(state).render(palette)
            print(HOME + frame + bell, end="", flush=True)
            next_frame = max(next_frame + FRAME_SECONDS, state["uptime"])
            wait_until(next_frame)
    except KeyboardInterrupt:
        pass
    finally:
        print(LEAVE_SCREEN, end="", flush=True)


# ---------------------------------------------------------------------------
# Questions asked before drawing
# ---------------------------------------------------------------------------

def ask(question, parse, default):
    """Keep asking until 'parse' accepts the answer; Enter keeps the default."""
    while True:
        try:
            answer = input(question).strip()
        except EOFError:
            print()
            return default
        if not answer:
            return default
        try:
            return parse(answer)
        except ValueError:
            print("  Valor no válido, intenta de nuevo.")



def parse_alarm(answer):
    """'7:30' or '07:30' -> seconds since midnight."""
    hours, minutes = (int(part) for part in answer.split(":"))
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError(answer)
    return hours * 3600 + minutes * 60


def parse_day_month(answer):
    """'24/12' -> (24, 12), validated against a leap year so 29/02 is allowed."""
    day, month = (int(part) for part in answer.split("/"))
    if not (1 <= month <= 12 and 1 <= day <= days_in_month(2024, month)):
        raise ValueError(answer)
    return day, month


def parse_theme(answer):
    index = int(answer) - 1
    if not 0 <= index < len(THEMES):
        raise ValueError(answer)
    return index


def choose_theme(state):
    for index, (name, palette) in enumerate(THEMES):
        print("   {}{}) {}{}".format(foreground(palette["accent"]), index + 1, name, RESET))
    state["theme"] = ask("  Tema: ", parse_theme, state["theme"])


def choose_alarm(state):
    state["alarm"] = ask("  Hora de la alarma (HH:MM, Enter para quitarla): ", parse_alarm, None)
    state["alarm_day"] = None


def toggle_stopwatch(state):
    uptime = read_uptime()
    if state["sw_started"] is None:
        state["sw_started"] = uptime
    else:
        state["sw_saved"] += uptime - state["sw_started"]
        state["sw_started"] = None


def reset_stopwatch(state):
    state["sw_started"], state["sw_saved"] = None, 0.0


def toggle_pomodoro(state):
    state["pomo_end"] = None if state["pomo_end"] is not None else read_uptime() + POMODORO_SECONDS


def choose_countdown(state):
    state["countdown"] = ask("  Fecha para la cuenta atrás (DD/MM, Enter para Navidad): ",
                             parse_day_month, (24, 12))


def toggle_reverse(state):
    state["reverse"] = not state["reverse"]


def spin_clock(state):
    state["spin_start"] = read_uptime()


MENU = [
    ("1", "Cambiar tema", choose_theme),
    ("2", "Programar o quitar la alarma", choose_alarm),
    ("3", "Cronómetro: iniciar o pausar", toggle_stopwatch),
    ("4", "Cronómetro: reiniciar", reset_stopwatch),
    ("5", "Pomodoro de 25 minutos: iniciar o cancelar", toggle_pomodoro),
    ("6", "Cambiar la fecha de la cuenta atrás", choose_countdown),
    ("7", "Reloj al revés: activar o desactivar", toggle_reverse),
    ("8", "¡Girar el reloj!", spin_clock),
]


def show_menu(state):
    """Print the options and run one; returns False when the user wants to quit."""
    palette = THEMES[state["theme"]][1]
    frame, title, muted = foreground(palette["frame"]), foreground(palette["highlight"]), \
        foreground(palette["muted"])
    print("\n{}╭──────────────── {}Menú del reloj{} ────────────────╮".format(frame, title, frame))
    for key, label, _ in MENU + [("0", "Salir", None)]:
        print("{}│{}  {}{}{}  {:<41}{}│".format(frame, RESET, title, key, RESET, label, frame))
    print("╰" + "─" * 48 + "╯" + RESET)
    print(muted + "  Enter vuelve al reloj." + RESET)
    try:
        choice = input("  Opción: ").strip()
    except (EOFError, KeyboardInterrupt):
        return False
    if choice == "0":
        return False
    for key, _, action in MENU:
        if choice == key:
            try:
                action(state)
            except KeyboardInterrupt:
                pass
    return True


def main():
    state = {"theme": 0, "boot": read_boot_time(), "zone": load_zone(None),
             "world": load_world(), "alarm": None, "alarm_day": None,
             "ringing_until": 0.0, "last_bell": -1, "sw_started": None, "sw_saved": 0.0,
             "pomo_end": None, "countdown": (24, 12),
             "reverse": False, "spin_start": -10.0}
    while True:
        run_clock(state)
        if is_ringing(state):
            state["ringing_until"] = 0.0   # Ctrl+C while ringing just silences it
            continue
        if not show_menu(state):
            break
    print("\n¡Hasta luego! 👋")

if __name__ == "__main__":
    main()
