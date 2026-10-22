"""Sine and cosine with Taylor series, so the math module is not needed."""

PI = 3.141592653589793
TAYLOR_TERMS = 12


def sin(angle: float) -> float:
    """Sine of an angle in radians, reduced to [-pi, pi] for precision."""
    angle = angle % (2 * PI)
    if angle > PI:
        angle -= 2 * PI
    term = total = angle
    for step in range(1, TAYLOR_TERMS):
        term *= -angle * angle / ((2 * step) * (2 * step + 1))
        total += term
    return total


def cos(angle: float) -> float:
    return sin(angle + PI / 2)


def polar(center_x: float, center_y: float, radius: float,
          degrees: float) -> tuple[float, float]:
    """Point on a clock dial: 0 degrees is 12 o'clock, growing clockwise (y grows down)."""
    radians = degrees * PI / 180
    return center_x + radius * sin(radians), center_y - radius * cos(radians)
