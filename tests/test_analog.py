from reloj.ui.analog import draw_analog_clock
from reloj.ui.canvas import BrailleCanvas


def labels(canvas):
    return "".join(character for _, _, character, _ in canvas.cells() if character.isdigit())


def test_all_twelve_numbers_are_drawn():
    canvas = BrailleCanvas(46, 23)
    draw_analog_clock(canvas, 0)
    text = labels(canvas)
    for hour in range(1, 13):
        assert str(hour) in text


def test_hands_point_to_the_time():
    canvas = BrailleCanvas(46, 23)
    draw_analog_clock(canvas, 3 * 3600)        # 03:00:00
    cells = {(row, column): color for row, column, _, color in canvas.cells()}
    # The hour hand runs from the center (row 11, column 23) to the right.
    assert cells[(11, 30)] == "ink"
    assert cells[(11, 16)] is None
