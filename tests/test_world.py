from reloj.core.dates import days_from_civil
from reloj.features.world import load_world_clocks

SUMMER_NOON_UTC = days_from_civil(2026, 7, 1) * 86400 + 12 * 3600


def test_loads_the_configured_cities():
    clocks = load_world_clocks([("Tokio", "Asia/Tokyo"), ("Madrid", "Europe/Madrid")])
    assert [clock.city for clock in clocks] == ["Tokio", "Madrid"]
    assert clocks[0].local_time(SUMMER_NOON_UTC).hour == 21
    assert clocks[1].local_time(SUMMER_NOON_UTC).hour == 14


def test_missing_zone_is_kept_as_unavailable():
    clock = load_world_clocks([("Atlántida", "Ocean/Atlantis")])[0]
    assert clock.zone is None
    assert clock.local_time(SUMMER_NOON_UTC) is None
