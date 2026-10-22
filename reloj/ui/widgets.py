"""Small reusable pieces of the dashboard."""

from reloj.ui.screen import Screen

BAR_PARTS = " ▏▎▍▌▋▊▉█"
LABEL_OFFSET, VALUE_OFFSET = 2, 15


def draw_border(screen: Screen, title: str, footer: str):
    """Rounded frame around the whole screen, with a title and a footer."""
    width, height = screen.width, screen.height
    screen.put(0, 0, "╭" + "─" * (width - 2) + "╮", "frame")
    for y in range(1, height - 1):
        screen.put(0, y, "│", "frame")
        screen.put(width - 1, y, "│", "frame")
    screen.put(0, height - 1, "╰" + "─" * (width - 2) + "╯", "frame")
    screen.put(3, 0, " " + title + " ", "highlight")
    screen.put(3, height - 1, " " + footer + " ", "muted")


def section_title(screen: Screen, y: int, title: str, left: int, right: int):
    """'──── Title ────' centered between two columns."""
    line = "─" * ((right - left - len(title) - 2) // 2)
    screen.center(y, "{} {} {}".format(line, title, line), "frame", left, right)


def draw_row(screen: Screen, left: int, y: int, label: str, value: str, detail: str = "",
             value_color="highlight"):
    """'Label        value  detail' row of the tools section."""
    screen.put(left + LABEL_OFFSET, y, label, "muted")
    screen.put(left + VALUE_OFFSET, y, value, value_color)
    screen.put(left + VALUE_OFFSET + len(value) + 2, y, detail, "muted")


def progress_bar(ratio: float, width: int) -> str:
    """Smooth bar drawn with eighth-width blocks."""
    eighths = int(max(0.0, min(1.0, ratio)) * width * 8)
    bar = "█" * (eighths // 8)
    if len(bar) < width:
        bar += BAR_PARTS[eighths % 8]
    return bar + " " * (width - len(bar))
