from reloj.ui.canvas import BrailleCanvas


def cell(canvas, row, column):
    for found_row, found_column, character, color in canvas.cells():
        if (found_row, found_column) == (row, column):
            return character, color
    raise AssertionError("cell not found")


def test_empty_cells_are_spaces():
    assert cell(BrailleCanvas(2, 1), 0, 0) == (" ", None)


def test_dots_map_to_braille_bits():
    canvas = BrailleCanvas(2, 1)
    canvas.dot(0, 0, "ink")
    canvas.dot(1, 3, "ink")
    assert cell(canvas, 0, 0) == (chr(0x2800 + 0x01 + 0x80), "ink")


def test_out_of_bounds_dots_are_ignored():
    canvas = BrailleCanvas(1, 1)
    canvas.dot(-2, 0, "ink")
    canvas.dot(2, 4, "ink")
    assert cell(canvas, 0, 0) == (" ", None)


def test_labels_cover_the_dots():
    canvas = BrailleCanvas(4, 1)
    canvas.line(0, 1, 7, 1, "ink")
    canvas.label(4, 1, "12", "accent")
    assert cell(canvas, 0, 1) == ("1", "accent")
    assert cell(canvas, 0, 2) == ("2", "accent")
    assert cell(canvas, 0, 0)[0] != " "
