from reloj.core.dates import LocalTime, days_from_civil
from reloj.core.system_clock import ClockReading
from reloj.features.toolbox import Toolbox
from reloj.features.world import load_world_clocks
from reloj.ui.dashboard import Dashboard
from reloj.ui.themes import THEMES

BOGOTA = -5 * 3600
EPOCH = days_from_civil(2026, 10, 22) * 86400 + 1 * 3600 + 23 * 60 + 45   # 20:23:45 local
READING = ClockReading(5000.0, EPOCH, LocalTime(EPOCH, BOGOTA))


def render(tools):
    return Dashboard().render(READING, THEMES[0], tools).text()


def test_screen_has_the_configured_size():
    lines = render(Toolbox(load_world_clocks())).splitlines()
    assert len(lines) == 27
    assert {len(line) for line in lines} == {100}


def test_shows_date_words_and_world_clocks():
    text = render(Toolbox(load_world_clocks()))
    assert "Jueves, 22 de octubre de 2026" not in text
    assert "Miércoles, 21 de octubre de 2026" in text
    assert "Son las ocho y veintitrés" in text
    assert "Tokio" in text and "10:23:45" in text


def test_alarm_banner_and_frame_flash():
    tools = Toolbox(world=[])
    tools.alarm.set(20 * 3600 + 23 * 60)
    tools.update(READING.local, READING.uptime)
    assert "¡ALARMA! Son las 20:23" in render(tools)
    palette = Dashboard().palette(THEMES[0], READING, tools)
    assert palette["frame"] == THEMES[0]["accent"]
