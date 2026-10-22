from reloj.features.stopwatch import Stopwatch


def test_starts_stopped():
    stopwatch = Stopwatch()
    assert not stopwatch.is_running
    assert stopwatch.elapsed(50) == 0


def test_pause_keeps_the_time_and_resume_adds_to_it():
    stopwatch = Stopwatch()
    stopwatch.toggle(10)
    assert stopwatch.elapsed(12.5) == 2.5
    stopwatch.toggle(13)            # pause at 3 s
    assert stopwatch.elapsed(100) == 3
    stopwatch.toggle(100)           # resume
    assert stopwatch.elapsed(101) == 4


def test_reset():
    stopwatch = Stopwatch()
    stopwatch.toggle(0)
    stopwatch.reset()
    assert not stopwatch.is_running
    assert stopwatch.elapsed(10) == 0
