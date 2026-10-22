from reloj.core.dates import LocalTime
from reloj.features.toolbox import Toolbox


def test_bell_follows_alarm_and_pomodoro():
    tools = Toolbox(world=[])
    assert not tools.wants_bell(0)
    tools.alarm.set(60)
    tools.update(LocalTime(60), uptime=0)
    assert tools.wants_bell(0)
    tools.alarm.silence()
    tools.pomodoro.toggle(0)
    assert tools.wants_bell(tools.pomodoro.focus_seconds + 1)
