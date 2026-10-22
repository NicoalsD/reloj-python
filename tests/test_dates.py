from reloj.core.dates import (LocalTime, civil_from_days, days_from_civil, days_in_month,
                              weekday_from_days)


def test_epoch_start_is_day_zero():
    assert days_from_civil(1970, 1, 1) == 0
    assert civil_from_days(0) == (1970, 1, 1)


def test_round_trip_over_many_centuries():
    for days in range(-800000, 800000, 997):
        assert days_from_civil(*civil_from_days(days)) == days


def test_known_dates():
    assert days_from_civil(2000, 3, 1) == 11017
    assert weekday_from_days(days_from_civil(2026, 10, 21)) == 3   # Wednesday


def test_days_in_month_handles_leap_years():
    assert days_in_month(2024, 2) == 29
    assert days_in_month(2026, 2) == 28
    assert days_in_month(2100, 2) == 28
    assert days_in_month(2026, 12) == 31


def test_local_time_applies_the_offset():
    moment = LocalTime(days_from_civil(2026, 10, 22) * 86400 + 3600, -5 * 3600)
    assert (moment.year, moment.month, moment.day) == (2026, 10, 21)
    assert (moment.hour, moment.minute, moment.second) == (20, 0, 0)
    assert moment.is_day(21, 10)
