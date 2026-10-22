from reloj.features.effects import Effects


def test_reverse_flips_the_direction():
    effects = Effects()
    assert effects.direction == 1
    effects.toggle_reverse()
    assert effects.direction == -1


def test_spin_goes_around_once_and_stops():
    effects = Effects(spin_seconds=2)
    assert effects.spin_angle(5) == 0
    effects.spin(10)
    assert effects.spin_angle(11) == 180
    assert effects.spin_angle(12) == 0


def test_rainbow_phase_only_when_enabled():
    effects = Effects(rainbow_period=4)
    assert effects.rainbow_phase(1) is None
    effects.toggle_rainbow()
    assert effects.rainbow_phase(1) == 0.25
    assert effects.rainbow_phase(5) == 0.25
