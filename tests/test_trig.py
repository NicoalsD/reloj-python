from reloj.core.trig import PI, cos, polar, sin


def close(first, second, tolerance=1e-9):
    return abs(first - second) < tolerance


def test_known_values():
    assert close(sin(0), 0)
    assert close(sin(PI / 2), 1)
    assert close(sin(PI / 6), 0.5)
    assert close(cos(PI), -1)


def test_large_and_negative_angles_are_reduced():
    assert close(sin(100 * PI + PI / 2), 1, 1e-6)
    assert close(sin(-PI / 2), -1)


def test_polar_follows_clock_directions():
    x, y = polar(0, 0, 10, 0)      # 12 o'clock is up
    assert close(x, 0) and close(y, -10)
    x, y = polar(0, 0, 10, 90)     # 3 o'clock is right
    assert close(x, 10) and close(y, 0)
