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
# SVG building helpers
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 1280, 800
SANS = "Helvetica, Arial, sans-serif"
MONO = "DejaVu Sans Mono, Menlo, Consolas, monospace"

THEMES = [
    ("Clásico", {"bg": "#f4f7fb", "face": "#ffffff", "ink": "#1f2a5a", "accent": "#e8402a",
                 "muted": "#8a90a6", "panel": "#ffffff", "highlight": "#8e2b8f"}),
    ("Neón", {"bg": "#0d0221", "face": "#1a0b3d", "ink": "#f4f1ff", "accent": "#ff2a6d",
              "muted": "#9d8fd6", "panel": "#170a33", "highlight": "#05d9e8"}),
    ("Matrix", {"bg": "#000000", "face": "#03170a", "ink": "#39ff14", "accent": "#c6ff00",
                "muted": "#1f8f3a", "panel": "#04140a", "highlight": "#00ff9c"}),
    ("Atardecer", {"bg": "#fde2c8", "face": "#fff7ef", "ink": "#4a1942", "accent": "#ff6b35",
                   "muted": "#b5838d", "panel": "#fff1e3", "highlight": "#e63946"}),
]


def number(value):
    """Format numbers compactly so the SVG stays small."""
    if isinstance(value, float):
        text = "{:.2f}".format(value).rstrip("0").rstrip(".")
        return "0" if text == "-0" else text
    return str(value)


def escape(content):
    return (str(content).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def tag(name, *children, **attributes):
    """Build an XML element; snake_case attribute names become kebab-case."""
    parts = [name]
    for key, value in attributes.items():
        if value is not None:
            parts.append('{}="{}"'.format(key.rstrip("_").replace("_", "-"),
                                          escape(number(value))))
    opening = " ".join(parts)
    if not children:
        return "<{}/>".format(opening)
    return "<{}>{}</{}>".format(opening, "".join(children), name)


def text(content, x, y, size, **attributes):
    attributes.setdefault("font_family", SANS)
    attributes.setdefault("text_anchor", "middle")
    attributes.setdefault("fill", color("ink"))
    return tag("text", escape(content), x=x, y=y, font_size=size, **attributes)


def color(role):
    """Every themed shape paints with a one-stop gradient, so themes can swap it."""
    return "url(#c-{})".format(role)


def build_palette(initial_theme):
    """One gradient per color role; clicking a theme button swaps every stop color."""
    gradients = []
    for role, value in THEMES[initial_theme][1].items():
        switches = [tag("set", attributeName="stop-color", to=palette[role],
                        begin="theme{}.click".format(index), fill="freeze")
                    for index, (_, palette) in enumerate(THEMES)]
        stop = tag("stop", *switches, offset=0, stop_color=value)
        gradients.append(tag("linearGradient", stop, id="c-" + role,
                             gradientUnits="userSpaceOnUse"))
    return "".join(gradients)


def build_theme_buttons():
    """Each button is painted with its own theme so it works as a preview."""
    y = 752
    parts = [text("Tema", 795, y + 6, 18, text_anchor="end", fill=color("muted"))]
    for index, (name, palette) in enumerate(THEMES):
        x = 810 + index * 110
        parts.append(tag("g",
                         tag("rect", x=x, y=y - 18, width=100, height=36, rx=18,
                             fill=palette["bg"], stroke=palette["accent"], stroke_width=2),
                         text(name, x + 50, y + 6, 16, fill=palette["ink"], font_weight="bold"),
                         id="theme{}".format(index), cursor="pointer"))
    return tag("g", *parts)


def build_header():
    return (text("Reloj en Python", 48, 70, 40, text_anchor="start", font_weight="bold")
            + text("100% Python puro · cero librerías · cero HTML/CSS", 50, 102, 18,
                   text_anchor="start", fill=color("muted")))


_id_counter = [0]


def unique_id(prefix):
    _id_counter[0] += 1
    return "{}-{}".format(prefix, _id_counter[0])


def past(offset):
    """SMIL begin value that starts an animation 'offset' seconds ago."""
    return "-{:.3f}s".format(offset)


def ticker(labels, x, y, size, step, begin, end=None, width=None, first=0,
           repeat="indefinite", **style):
    """Odometer: a column of labels behind a one-line window that jumps every 'step' s.

    Before 'begin' (or after the animation ends) the label at index 0 is shown;
    while running it walks from index 'first' to the last one.
    """
    clip_id = unique_id("clip")
    line = size * 1.4
    if width is None:
        width = size * (0.62 * max(len(str(label)) for label in labels) + 0.2)
    style.setdefault("font_family", MONO)
    window = tag("clipPath", tag("rect", x=x - width / 2, y=y - size * 0.95,
                                 width=width, height=size * 1.25), id=clip_id)
    labels_svg = [text(label, x, y + index * line, size, **style)
                  for index, label in enumerate(labels)]
    shown = range(first, len(labels))
    values = ";".join("0 {}".format(number(-index * line)) for index in shown)
    motion = tag("animateTransform", attributeName="transform", type="translate",
                 values=values, calcMode="discrete", dur="{}s".format(number(step * len(shown))),
                 begin=begin, end=end, repeatCount=repeat)
    return window + tag("g", tag("g", *(labels_svg + [motion])),
                        clip_path="url(#{})".format(clip_id))


def two_digits(count):
    return ["{:02d}".format(value) for value in range(count)]


def build_dial(cx, cy, radius, direction=1, with_numbers=True):
    """Clock face: rim, 60 minute ticks, thicker hour ticks and 1 to 12."""
    parts = [tag("circle", cx=cx, cy=cy, r=radius, fill=color("face"),
                 stroke=color("ink"), stroke_width=max(2.0, radius / 70))]
    for tick in range(60):
        is_hour = tick % 5 == 0
        inner = radius * (0.86 if is_hour else 0.92)
        x1, y1 = polar(cx, cy, inner, tick * 6 * direction)
        x2, y2 = polar(cx, cy, radius * 0.97, tick * 6 * direction)
        parts.append(tag("line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=color("ink"),
                         stroke_width=radius / (55 if is_hour else 150),
                         stroke_linecap="round"))
    if with_numbers:
        size = radius * 0.15
        for hour in range(1, 13):
            x, y = polar(cx, cy, radius * 0.72, hour * 30 * direction)
            parts.append(text(hour, x, y + size * 0.36, size))
    return tag("g", *parts)


def points(*pairs):
    return " ".join("{},{}".format(number(float(x)), number(float(y))) for x, y in pairs)


def rotation(cx, cy, duration, offset, direction=1, ticks=0, begin=None, end=None):
    """Endless SMIL rotation around (cx, cy).

    A negative begin time starts the animation 'offset' seconds in the past,
    which is how the hands start exactly at the current time.
    """
    if ticks:
        values = ";".join("{} {} {}".format(number(360.0 * step / ticks * direction), cx, cy)
                          for step in range(ticks))
        mode = "discrete"
    else:
        values = "0 {cx} {cy};{turn} {cx} {cy}".format(cx=cx, cy=cy, turn=360 * direction)
        mode = "linear"
    return tag("animateTransform", attributeName="transform", type="rotate", values=values,
               calcMode=mode, dur="{}s".format(duration),
               begin=begin or "-{:.3f}s".format(offset), end=end, repeatCount="indefinite")


def build_hands(cx, cy, radius, seconds_of_day, direction=1, with_seconds=True):
    """Hour, minute and second hands, all drawn pointing at 12 and then rotated."""
    hour = tag("g", tag("polygon", fill=color("ink"), points=points(
        (cx, cy + radius * 0.08), (cx - radius * 0.035, cy),
        (cx, cy - radius * 0.5), (cx + radius * 0.035, cy))),
        rotation(cx, cy, 43200, seconds_of_day % 43200, direction))
    minute = tag("g", tag("polygon", fill=color("ink"), points=points(
        (cx, cy + radius * 0.1), (cx - radius * 0.022, cy),
        (cx, cy - radius * 0.82), (cx + radius * 0.022, cy))),
        rotation(cx, cy, 3600, seconds_of_day % 3600, direction))
    parts = [hour, minute]
    if with_seconds:
        parts.append(tag("g",
                         tag("line", x1=cx, y1=cy + radius * 0.18, x2=cx, y2=cy - radius * 0.9,
                             stroke=color("accent"), stroke_width=max(1.2, radius / 120),
                             stroke_linecap="round"),
                         tag("circle", cx=cx, cy=cy + radius * 0.14, r=radius * 0.025,
                             fill=color("accent")),
                         rotation(cx, cy, 60, seconds_of_day % 60, direction, ticks=60)))
    parts.append(tag("circle", cx=cx, cy=cy, r=radius * 0.035, fill=color("ink")))
    parts.append(tag("circle", cx=cx, cy=cy, r=radius * 0.014, fill=color("accent")))
    return tag("g", *parts)


CLOCK_X, CLOCK_Y, CLOCK_RADIUS = 380, 445, 290


def build_main_clock(state):
    shadow = tag("filter", tag("feDropShadow", dx=0, dy=10, stdDeviation=14,
                               flood_color="#000000", flood_opacity=0.22),
                 id="shadow", x="-20%", y="-20%", width="140%", height="140%")
    seconds = state["now"]["seconds_of_day"]
    return tag("g", shadow,
               tag("g", build_dial(CLOCK_X, CLOCK_Y, CLOCK_RADIUS), filter="url(#shadow)"),
               build_hands(CLOCK_X, CLOCK_Y, CLOCK_RADIUS, seconds), id="main-clock")


PANEL_X = 1000


def build_digital(state):
    """Live HH:MM:SS made of three odometers plus blinking colons."""
    seconds = state["now"]["seconds_of_day"]
    y, size = 175, 84
    parts = [
        ticker(two_digits(24), PANEL_X - 148, y, size, 3600, past(seconds), font_weight="bold"),
        ticker(two_digits(60), PANEL_X, y, size, 60, past(seconds % 3600), font_weight="bold"),
        ticker(two_digits(60), PANEL_X + 148, y, size, 1, past(seconds % 60),
               font_weight="bold", fill=color("accent")),
    ]
    blink = tag("animate", attributeName="opacity", values="1;0.25", calcMode="discrete",
                dur="1s", begin=past(seconds % 1), repeatCount="indefinite")
    for x in (PANEL_X - 74, PANEL_X + 74):
        parts.append(tag("text", ":", blink, x=x, y=y - 8, font_size=size,
                         font_family=MONO, text_anchor="middle", fill=color("muted")))
    date = format_date(state["now"])
    parts.append(text(date[0].upper() + date[1:], PANEL_X, y + 55, 24, fill=color("muted")))
    return tag("g", *parts)


def greeting(hour):
    if hour < 6:
        return "¡A dormir, búho nocturno! 🦉"
    if hour < 12:
        return "¡Buenos días! ☀️"
    if hour < 14:
        return "¡Hora de almorzar! 🍽️"
    if hour < 19:
        return "¡Buenas tardes! 🌤️"
    return "¡Buenas noches! 🌙"


def build_greeting(state):
    """Greeting that changes on its own every hour."""
    seconds = state["now"]["seconds_of_day"]
    labels = [greeting(hour) for hour in range(24)]
    return ticker(labels, PANEL_X, 268, 26, 3600, past(seconds), width=480,
                  font_family=SANS, fill=color("highlight"), font_weight="bold")


CARD_X, CARD_Y, CARD_WIDTH, CARD_HEIGHT = 760, 355, 480, 360


def switch_visibility(key, keys):
    """<set> elements that show a panel when its tab is clicked and hide it otherwise.

    SMIL ids are written without '-' because 'a-1.click' would read as an offset.
    """
    return [tag("set", attributeName="visibility", to="visible" if other == key else "hidden",
                begin="tab{}.click".format(other), fill="freeze") for other in keys]


def build_tabs(panels):
    """Tab buttons plus one card per panel; only the first one starts visible."""
    keys = [key for key, _, _ in panels]
    width, gap = 112, 10
    parts = [tag("rect", x=CARD_X, y=CARD_Y, width=CARD_WIDTH, height=CARD_HEIGHT, rx=18,
                 fill=color("panel"), stroke=color("muted"), stroke_opacity=0.4)]
    for index, (key, label, content) in enumerate(panels):
        x = CARD_X + index * (width + gap)
        visible = "visible" if index == 0 else "hidden"
        active_outline = tag("rect", *switch_visibility(key, keys), x=x, y=CARD_Y - 50,
                             width=width, height=38, rx=12, fill="none",
                             stroke=color("highlight"), stroke_width=3, visibility=visible)
        parts.append(tag("g",
                         tag("rect", x=x, y=CARD_Y - 50, width=width, height=38, rx=12,
                             fill=color("panel"), stroke=color("muted"), stroke_width=1.5),
                         active_outline,
                         text(label, x + width / 2, CARD_Y - 26, 14, font_weight="bold"),
                         id="tab" + key, cursor="pointer"))
        parts.append(tag("g", *([content] + switch_visibility(key, keys)), visibility=visible))
    return tag("g", *parts)


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


def build_world_clock(city, zone_name, cx, cy, state):
    try:
        offset = zone_offset(load_zone(zone_name), state["epoch"])[0]
    except (OSError, ValueError):
        return text(city + ": zona no disponible", cx, cy, 14, fill=color("muted"))
    moment = local_datetime(state["epoch"], offset)
    seconds = moment["seconds_of_day"]
    radius, size, y = 52, 15, cy + 98
    details = "{} · {}".format(format_utc_offset(offset),
                               relative_day(moment["days"], state["now"]["days"]))
    return tag("g",
               build_dial(cx, cy, radius, with_numbers=False),
               build_hands(cx, cy, radius, seconds),
               text(city, cx, cy + 77, 18, font_weight="bold"),
               ticker(two_digits(24), cx - 62, y, size, 3600, past(seconds)),
               text(":", cx - 50, y, size, font_family=MONO),
               ticker(two_digits(60), cx - 38, y, size, 60, past(seconds % 3600)),
               text(details, cx - 20, y, 13, text_anchor="start", fill=color("muted")))


def build_world_panel(state):
    parts = []
    for index, (city, zone_name) in enumerate(WORLD_ZONES):
        cx = CARD_X + 120 + (index % 2) * 240
        cy = CARD_Y + 75 + (index // 2) * 170
        parts.append(build_world_clock(city, zone_name, cx, cy, state))
    return tag("g", *parts)


def build_button(element_id, label, x, y, width=130):
    return tag("g",
               tag("rect", x=x, y=y, width=width, height=40, rx=20, fill=color("highlight")),
               text(label, x + width / 2, y + 26, 17, fill=color("panel"), font_weight="bold"),
               id=element_id, cursor="pointer")


def build_stopwatch_panel():
    """Starts on 'Iniciar' (clicking again restarts) and goes back to zero on 'Reiniciar'."""
    cx, cy, radius = CARD_X + CARD_WIDTH / 2, CARD_Y + 120, 95
    start, stop = "swStart.click", "swReset.click"
    parts = [build_dial(cx, cy, radius, with_numbers=False)]
    for step in range(1, 13):
        x, y = polar(cx, cy, radius * 0.7, step * 30)
        parts.append(text(step * 5, x, y + 5, 14, fill=color("muted")))
    parts.append(tag("g",
                     tag("line", x1=cx, y1=cy + 15, x2=cx, y2=cy - radius * 0.9,
                         stroke=color("accent"), stroke_width=2.5, stroke_linecap="round"),
                     rotation(cx, cy, 60, 0, begin=start, end=stop)))
    parts.append(tag("circle", cx=cx, cy=cy, r=5, fill=color("accent")))
    y, size = CARD_Y + 268, 40
    parts += [
        ticker(two_digits(60), cx - 72, y, size, 60, start, stop, font_weight="bold"),
        text(":", cx - 36, y - 3, size, font_family=MONO),
        ticker(two_digits(60), cx, y, size, 1, start, stop, font_weight="bold"),
        text(".", cx + 34, y, size, font_family=MONO),
        ticker([str(tenth) for tenth in range(10)], cx + 60, y, size, 0.1, start, stop,
               font_weight="bold", fill=color("accent")),
        build_button("swStart", "▶ Iniciar", cx - 140, CARD_Y + 300),
        build_button("swReset", "↺ Reiniciar", cx + 10, CARD_Y + 300),
    ]
    return tag("g", *parts)


POMODORO_MINUTES = 25


def build_pomodoro_panel():
    """25 minute focus timer: a ring that empties and a countdown in the middle."""
    cx, cy, radius = CARD_X + CARD_WIDTH / 2, CARD_Y + 120, 95
    total = POMODORO_MINUTES * 60
    start, stop = "pomoStart.click", "pomoReset.click"
    circumference = 2 * PI * radius
    progress = tag("circle",
                   tag("animate", attributeName="stroke-dashoffset", values="0;{}".format(
                       number(circumference)), dur="{}s".format(total), begin=start, end=stop),
                   cx=cx, cy=cy, r=radius, fill="none", stroke=color("accent"), stroke_width=14,
                   stroke_linecap="round", stroke_dasharray=number(circumference),
                   transform="rotate(-90 {} {})".format(cx, cy))
    minutes = ["{:02d}".format(POMODORO_MINUTES - index) for index in range(POMODORO_MINUTES + 1)]
    seconds = ["{:02d}".format((60 - index) % 60) for index in range(60)]
    size = 44
    done = tag("set", attributeName="visibility", to="visible",
               begin="{}+{}s".format(start, total), end=stop, dur="120s")
    return tag("g",
               tag("circle", cx=cx, cy=cy, r=radius, fill=color("face"), stroke=color("muted"),
                   stroke_opacity=0.3, stroke_width=14),
               progress,
               ticker(minutes, cx - 38, cy + 15, size, 60, "{}+1s".format(start), stop,
                      first=1, repeat=None, font_weight="bold"),
               text(":", cx, cy + 12, size, font_family=MONO),
               ticker(seconds, cx + 38, cy + 15, size, 1, start, stop,
                      repeat=POMODORO_MINUTES, font_weight="bold"),
               text("🍅 {} minutos de enfoque".format(POMODORO_MINUTES), cx, CARD_Y + 250, 18,
                    fill=color("muted")),
               tag("g", text("¡Tiempo cumplido! Descansa 5 minutos ☕", cx, CARD_Y + 280, 20,
                             fill=color("accent"), font_weight="bold"),
                   done, visibility="hidden"),
               build_button("pomoStart", "▶ Iniciar", cx - 140, CARD_Y + 300),
               build_button("pomoReset", "↺ Reiniciar", cx + 10, CARD_Y + 300))


def build_panels(state):
    center = CARD_X + CARD_WIDTH / 2
    return build_tabs([
        ("world", "🌎 Mundo", build_world_panel(state)),
        ("stopwatch", "⏱️ Cronómetro", build_stopwatch_panel()),
        ("pomodoro", "🍅 Pomodoro", build_pomodoro_panel()),
        ("fun", "🎉 Divertido", text("Modo divertido", center, 540, 22)),
    ])


def build_alarm_marker(state):
    """Small triangle outside the rim pointing at the alarm hour, plus a caption."""
    alarm = state.get("alarm")
    if alarm is None:
        return text("⏰ Sin alarma", 50, 135, 16, text_anchor="start", fill=color("muted"))
    angle = alarm % 43200 / 120.0
    tip = polar(CLOCK_X, CLOCK_Y, CLOCK_RADIUS + 6, angle)
    left = polar(CLOCK_X, CLOCK_Y, CLOCK_RADIUS + 24, angle - 2.5)
    right = polar(CLOCK_X, CLOCK_Y, CLOCK_RADIUS + 24, angle + 2.5)
    return tag("g",
               tag("polygon", points=points(tip, left, right), fill=color("accent")),
               text("⏰ Alarma a las {}".format(format_clock(alarm)), 50, 135, 16,
                    text_anchor="start", fill=color("accent"), font_weight="bold"))


def build_alarm_overlay(state):
    """Hidden full screen banner that pops up when the alarm time arrives."""
    alarm = state.get("alarm")
    if alarm is None:
        return ""
    delay = (alarm - state["now"]["seconds_of_day"]) % SECONDS_PER_DAY
    begin = "{:.3f}s;{:.3f}s".format(delay, delay + SECONDS_PER_DAY)
    flash = tag("animate", attributeName="opacity", values="0.92;0.7;0.92", dur="0.8s",
                repeatCount="indefinite")
    bell = tag("g", text("⏰", WIDTH / 2, HEIGHT / 2 - 70, 120, fill="#ffffff"),
               tag("animateTransform", attributeName="transform", type="rotate",
                   values="-15 {x} {y};15 {x} {y};-15 {x} {y}".format(x=WIDTH / 2, y=HEIGHT / 2 - 110),
                   dur="0.4s", repeatCount="indefinite"))
    return tag("g",
               tag("rect", flash, width=WIDTH, height=HEIGHT, fill=color("accent")),
               bell,
               text("¡Alarma! Son las " + format_clock(alarm), WIDTH / 2, HEIGHT / 2 + 40, 64,
                    fill="#ffffff", font_weight="bold"),
               text("Haz clic en cualquier parte para apagarla", WIDTH / 2, HEIGHT / 2 + 95, 24,
                    fill="#ffffff"),
               tag("set", attributeName="visibility", to="visible", begin=begin, dur="60s"),
               tag("set", attributeName="visibility", to="hidden", begin="alarmOverlay.click",
                   dur="60s"),
               id="alarmOverlay", visibility="hidden", cursor="pointer")


def build_svg(state):
    body = [
        tag("defs", build_palette(state.get("theme", 0))),
        tag("rect", width=WIDTH, height=HEIGHT, fill=color("bg")),
        build_header(),
        build_main_clock(state),
        build_digital(state),
        build_greeting(state),
        build_panels(state),
        build_theme_buttons(),
        build_alarm_marker(state),
        build_alarm_overlay(state),
    ]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            + tag("svg", *body, xmlns="http://www.w3.org/2000/svg",
                  viewBox="0 0 {} {}".format(WIDTH, HEIGHT)))


def output_path():
    """Write next to this script (__file__ is absolute since Python 3.9)."""
    folder = __file__.rpartition("/")[0]
    return (folder + "/" if folder else "") + OUTPUT_FILE


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


def parse_theme(answer):
    index = int(answer) - 1
    if not 0 <= index < len(THEMES):
        raise ValueError(answer)
    return index


def parse_alarm(answer):
    """'7:30' or '07:30' -> seconds since midnight."""
    hours, minutes = (int(part) for part in answer.split(":"))
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError(answer)
    return hours * 3600 + minutes * 60


def main():
    print("🕰️  Reloj en Python\n")
    names = " ".join("{}) {}".format(index + 1, name) for index, (name, _) in enumerate(THEMES))
    theme = ask("Tema inicial: {} [1]: ".format(names), parse_theme, 0)
    alarm = ask("Hora de la alarma (HH:MM, Enter para ninguna): ", parse_alarm, None)

    # Read the clock only after the questions so the drawing starts on time.
    epoch = read_epoch()
    offset, _, zone_name = zone_offset(load_zone(None), epoch)
    now = local_datetime(epoch, offset)
    state = {"epoch": epoch, "now": now, "theme": theme, "alarm": alarm}
    path = output_path()
    with open(path, "w", encoding="utf-8") as target:
        target.write(build_svg(state))
    print("\nHora local ({}): {} {}".format(zone_name, format_date(now), format_time(now)))
    print("Reloj generado en: file://" + path)
    print("Ábrelo ya en tu navegador; si lo abres más tarde, vuelve a generarlo.")


if __name__ == "__main__":
    main()
