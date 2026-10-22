"""RGB helpers and 24-bit ANSI color codes."""

ESCAPE = "\x1b["
RESET = ESCAPE + "0m"

RGB = tuple[int, int, int]


def foreground(rgb: RGB) -> str:
    return ESCAPE + "38;2;{};{};{}m".format(*rgb)


def background(rgb: RGB) -> str:
    return ESCAPE + "48;2;{};{};{}m".format(*rgb)


def mix(first: RGB, second: RGB, ratio: float) -> RGB:
    """Blend two colors; ratio 0 gives 'first' and 1 gives 'second'."""
    return tuple(int(a + (b - a) * ratio) for a, b in zip(first, second))


def hue_color(hue: float) -> RGB:
    """Bright color for a hue in [0, 1), without the colorsys module."""
    sector = int(hue * 6) % 6
    rise = hue * 6 - int(hue * 6)
    fall = 1 - rise
    channels = [(1, rise, 0), (fall, 1, 0), (0, 1, rise),
                (0, fall, 1), (rise, 0, 1), (1, 0, fall)][sector]
    return tuple(int(80 + 175 * value) for value in channels)
