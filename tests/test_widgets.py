from reloj.ui.screen import Screen
from reloj.ui.widgets import draw_border, draw_row, progress_bar, section_title


def test_progress_bar_keeps_its_width():
    assert progress_bar(0, 4) == "    "
    assert progress_bar(1, 4) == "████"
    assert progress_bar(0.5, 4) == "██  "
    assert progress_bar(0.25 + 1 / 32, 4) == "█▏  "
    assert progress_bar(2, 4) == "████"


def test_border_and_title():
    screen = Screen(12, 3)
    draw_border(screen, "Hi", "Ok")
    assert screen.text() == "╭── Hi ────╮\n│          │\n╰── Ok ────╯"


def test_section_title_and_row():
    screen = Screen(20, 2)
    section_title(screen, 0, "Mundo", 0, 20)
    draw_row(screen, 0, 1, "A", "07:30", "x")
    assert screen.text().splitlines() == ["────── Mundo ────── ", "  A            07:30"]
