"""Analog clock drawn on a braille canvas.

'direction' is 1 for a normal clock and -1 for one that runs counterclockwise;
'turn' rotates the whole dial in degrees (used by the spin effect).
"""

from reloj.core.trig import polar
from reloj.ui.canvas import BrailleCanvas


def draw_analog_clock(canvas: BrailleCanvas, seconds_of_day: float,
                      direction: int = 1, turn: float = 0.0):
    draw_dial(canvas, direction, turn)
    draw_hands(canvas, seconds_of_day, direction, turn)


def draw_dial(canvas: BrailleCanvas, direction: int = 1, turn: float = 0.0):
    """Rim, minute dots, hour ticks and the numbers 1 to 12."""
    cx, cy, radius = _geometry(canvas)
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


def draw_hands(canvas: BrailleCanvas, seconds_of_day: float,
               direction: int = 1, turn: float = 0.0):
    """Hour and minute hands move smoothly; the second hand jumps like a real one."""
    cx, cy, radius = _geometry(canvas)
    hour = (seconds_of_day % 43200) / 120.0 * direction + turn
    minute = (seconds_of_day % 3600) / 10.0 * direction + turn
    second = int(seconds_of_day % 60) * 6 * direction + turn
    canvas.line(cx, cy, *polar(cx, cy, radius * 0.48, hour), color="ink", thickness=1.5)
    canvas.line(cx, cy, *polar(cx, cy, radius * 0.76, minute), color="ink", thickness=0.5)
    canvas.line(*(polar(cx, cy, radius * 0.18, second + 180) + polar(cx, cy, radius * 0.86, second)),
                color="accent")
    for ring in (0.5, 1.2, 2.0):
        canvas.circle(cx, cy, ring, "accent")


def _geometry(canvas: BrailleCanvas) -> tuple[float, float, float]:
    """Center and radius that fit the canvas with a small margin."""
    cx, cy = canvas.width / 2, canvas.height / 2
    return cx, cy, min(cx, cy) - 2
