from reloj.ui.colors import background, foreground, hue_color, mix


def test_escape_codes():
    assert foreground((1, 2, 3)) == "\x1b[38;2;1;2;3m"
    assert background((4, 5, 6)) == "\x1b[48;2;4;5;6m"


def test_mix():
    assert mix((0, 0, 0), (100, 200, 50), 0) == (0, 0, 0)
    assert mix((0, 0, 0), (100, 200, 50), 0.5) == (50, 100, 25)


def test_hue_color_main_points():
    assert hue_color(0) == (255, 80, 80)          # red
    assert hue_color(1 / 3) == (80, 255, 80)      # green
    assert hue_color(2 / 3) == (80, 80, 255)      # blue
