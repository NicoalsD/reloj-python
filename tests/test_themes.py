from reloj.ui.themes import THEMES, Theme

ROLES = {"bg", "ink", "accent", "muted", "highlight", "frame"}


def test_every_theme_defines_every_role():
    for theme in THEMES:
        assert set(theme.colors) == ROLES, theme.name


def test_with_colors_does_not_change_the_original():
    theme = Theme("Prueba", bg=(0, 0, 0), frame=(1, 1, 1))
    flashed = theme.with_colors(frame=(9, 9, 9))
    assert flashed["frame"] == (9, 9, 9)
    assert theme["frame"] == (1, 1, 1)
    assert flashed["bg"] == (0, 0, 0)
