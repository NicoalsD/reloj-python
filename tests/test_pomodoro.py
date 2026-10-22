from reloj.features.pomodoro import BREAK, FOCUS, IDLE, Pomodoro


def test_full_cycle():
    pomodoro = Pomodoro(focus_seconds=100, break_seconds=30, bell_seconds=3)
    assert pomodoro.phase(0) == IDLE
    pomodoro.toggle(0)
    assert pomodoro.phase(40) == FOCUS
    assert pomodoro.remaining(40) == 60
    assert pomodoro.progress(40) == 0.4
    assert pomodoro.phase(100) == BREAK
    assert pomodoro.wants_bell(101) and not pomodoro.wants_bell(104)
    pomodoro.update(129)
    assert pomodoro.phase(129) == BREAK
    pomodoro.update(131)
    assert pomodoro.phase(131) == IDLE


def test_toggle_cancels():
    pomodoro = Pomodoro(focus_seconds=100)
    pomodoro.toggle(0)
    pomodoro.toggle(10)
    assert pomodoro.phase(10) == IDLE
    assert not pomodoro.wants_bell(100)
