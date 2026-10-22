from reloj.core.parsing import parse_choice, parse_clock_time, parse_day_month


def raises_value_error(parser, *arguments):
    try:
        parser(*arguments)
    except ValueError:
        return True
    return False


def test_clock_time():
    assert parse_clock_time("7:30") == 27000
    assert parse_clock_time("00:00") == 0
    for wrong in ("24:00", "7:60", "7", "a:b", "1:2:3"):
        assert raises_value_error(parse_clock_time, wrong), wrong


def test_day_month():
    assert parse_day_month("24/12") == (24, 12)
    assert parse_day_month("29/2") == (29, 2)
    for wrong in ("31/02", "0/1", "1/13", "14/2/3", "hoy"):
        assert raises_value_error(parse_day_month, wrong), wrong


def test_choice():
    assert parse_choice("1", 5) == 0
    assert parse_choice("5", 5) == 4
    assert raises_value_error(parse_choice, "6", 5)
    assert raises_value_error(parse_choice, "0", 5)
