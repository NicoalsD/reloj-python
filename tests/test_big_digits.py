from reloj.ui.big_digits import FONT, FONT_HEIGHT, big_text


def test_every_glyph_is_rectangular():
    for character, rows in FONT.items():
        assert len(rows) == FONT_HEIGHT, character
        assert len({len(row) for row in rows}) == 1, character


def test_time_width_fits_the_panel():
    rows = big_text("23:59:59")
    assert len(rows) == FONT_HEIGHT
    assert len(rows[0]) == 6 * 5 + 2 * 3 + 7
