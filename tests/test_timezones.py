from reloj.core.dates import days_from_civil
from reloj.core.timezones import PosixRule, TimeZone

SUMMER_2026 = days_from_civil(2026, 7, 1) * 86400
WINTER_2026 = days_from_civil(2026, 1, 15) * 86400
FAR_FUTURE = days_from_civil(2050, 7, 1) * 86400


def test_rule_without_daylight_saving():
    rule = PosixRule("<-05>5")
    assert rule.state_at(SUMMER_2026).offset == -5 * 3600
    assert rule.state_at(SUMMER_2026).name == "-05"


def test_european_rule_switches_in_march_and_october():
    rule = PosixRule("CET-1CEST,M3.5.0,M10.5.0/3")
    assert rule.state_at(SUMMER_2026).offset == 2 * 3600
    assert rule.state_at(WINTER_2026).offset == 3600
    # DST ends on the last Sunday of October 2026 (the 25th) at 01:00 UTC.
    change = days_from_civil(2026, 10, 25) * 86400 + 3600
    assert rule.state_at(change - 1).is_dst
    assert not rule.state_at(change).is_dst


def test_southern_hemisphere_rule():
    rule = PosixRule("AEST-10AEDT,M10.1.0,M4.1.0/3")
    assert rule.state_at(WINTER_2026).name == "AEDT"
    assert rule.state_at(SUMMER_2026).name == "AEST"


def test_zoneinfo_files_match_the_rules():
    madrid = TimeZone.named("Europe/Madrid")
    assert madrid.offset_at(SUMMER_2026) == 7200
    assert madrid.offset_at(WINTER_2026) == 3600
    assert madrid.offset_at(FAR_FUTURE) == 7200
    assert TimeZone.named("Asia/Tokyo").offset_at(SUMMER_2026) == 9 * 3600
    assert TimeZone.named("America/New_York").state_at(WINTER_2026).name == "EST"


def test_rejects_files_that_are_not_tzif():
    try:
        TimeZone.from_bytes(b"hello")
    except ValueError:
        return
    raise AssertionError("ValueError expected")
