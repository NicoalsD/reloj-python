from reloj.ui.screen import Screen
from reloj.ui.themes import Theme

THEME = Theme("Prueba", bg=(0, 0, 0), ink=(1, 1, 1), accent=(2, 2, 2))


def test_put_clips_at_the_edges():
    screen = Screen(4, 2)
    screen.put(2, 0, "hola")
    screen.put(0, 5, "nada")
    assert screen.text() == "  ho\n    "


def test_center():
    screen = Screen(6, 1)
    screen.center(0, "ab")
    assert screen.text() == "  ab  "


def test_render_changes_color_only_when_needed():
    screen = Screen(3, 1)
    screen.put(0, 0, "ab", "accent")
    frame = screen.render(THEME)
    assert frame == ("\x1b[48;2;0;0;0m\x1b[38;2;2;2;2mab"
                     "\x1b[38;2;1;1;1m \x1b[0m")
