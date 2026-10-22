from reloj.core.dates import LocalTime
from reloj.features.alarm import Alarm

SEVEN_THIRTY = 7 * 3600 + 30 * 60


def at(seconds_of_day, day=0):
    return LocalTime(day * 86400 + seconds_of_day)


def test_rings_during_the_alarm_minute():
    alarm = Alarm(ring_seconds=60)
    alarm.set(SEVEN_THIRTY)
    alarm.update(at(SEVEN_THIRTY - 1), uptime=100)
    assert not alarm.is_ringing(100)
    alarm.update(at(SEVEN_THIRTY + 5), uptime=101)
    assert alarm.is_ringing(101)
    assert not alarm.is_ringing(161)


def test_silenced_alarm_does_not_ring_again_the_same_day():
    alarm = Alarm()
    alarm.set(SEVEN_THIRTY)
    alarm.update(at(SEVEN_THIRTY), uptime=0)
    alarm.silence()
    alarm.update(at(SEVEN_THIRTY + 10), uptime=10)
    assert not alarm.is_ringing(10)
    alarm.update(at(SEVEN_THIRTY, day=1), uptime=86400)
    assert alarm.is_ringing(86400)


def test_seconds_left_wraps_around_midnight():
    alarm = Alarm()
    alarm.set(SEVEN_THIRTY)
    assert alarm.seconds_left(at(SEVEN_THIRTY - 60)) == 60
    assert alarm.seconds_left(at(SEVEN_THIRTY + 60)) == 86400 - 60


def test_without_time_it_never_rings():
    alarm = Alarm()
    alarm.update(at(0), uptime=0)
    assert not alarm.is_ringing(0)
