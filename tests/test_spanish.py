from reloj.core.dates import LocalTime, days_from_civil
from reloj.core.spanish import (format_clock, format_date, format_duration, format_time,
                                format_utc_offset, greeting, relative_day, time_in_words)

OCTOBER_21_AT_20_10 = days_from_civil(2026, 10, 21) * 86400 + 20 * 3600 + 10 * 60 + 5


def test_long_date_is_capitalized():
    assert format_date(LocalTime(OCTOBER_21_AT_20_10)) == "Miércoles, 21 de octubre de 2026"


def test_times_and_durations():
    assert format_time(LocalTime(OCTOBER_21_AT_20_10)) == "20:10:05"
    assert format_clock(7 * 3600 + 30 * 60) == "07:30"
    assert format_duration(9 * 3600 + 5 * 60) == "9 h 05 min"
    assert format_duration(270) == "4 min 30 s"


def test_utc_offsets():
    assert format_utc_offset(-5 * 3600) == "UTC-5"
    assert format_utc_offset(5 * 3600 + 1800) == "UTC+5:30"


def test_relative_days_and_greetings():
    assert relative_day(11, 10) == "mañana"
    assert relative_day(9, 10) == "ayer"
    assert greeting(3) == "¡A dormir, búho nocturno!"
    assert greeting(20) == "¡Buenas noches!"


def test_time_in_words():
    assert time_in_words(0, 0) == "Son las doce en punto"
    assert time_in_words(13, 15) == "Es la una y cuarto"
    assert time_in_words(13, 30) == "Es la una y media"
    assert time_in_words(12, 45) == "Es la una menos cuarto"
    assert time_in_words(15, 1) == "Son las tres y uno"
    assert time_in_words(23, 59) == "Son las doce menos uno"
