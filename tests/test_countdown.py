from reloj.core.dates import LocalTime, days_from_civil
from reloj.features.countdown import Countdown

BOGOTA = -5 * 3600


def local_at(year, month, day, hour=0):
    epoch = days_from_civil(year, month, day) * 86400 + hour * 3600 - BOGOTA
    return LocalTime(epoch, BOGOTA)


def test_counts_to_local_midnight():
    countdown = Countdown(24, 12)
    assert countdown.seconds_left(local_at(2026, 12, 23, hour=12)) == 12 * 3600


def test_past_dates_count_to_next_year():
    countdown = Countdown(1, 1)
    now = local_at(2026, 10, 21)
    assert countdown.seconds_left(now) == (days_from_civil(2027, 1, 1)
                                           - days_from_civil(2026, 10, 21)) * 86400


def test_today_and_leap_days():
    assert Countdown(21, 10).is_today(local_at(2026, 10, 21, hour=8))
    leap = Countdown(29, 2)
    expected = days_from_civil(2028, 2, 29) * 86400 - BOGOTA
    assert leap.target_epoch(local_at(2026, 3, 1)) == expected
