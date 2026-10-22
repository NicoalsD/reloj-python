from reloj.core.system_clock import SystemClock


class FixedOffsetZone:
    def offset_at(self, epoch):
        return -5 * 3600


def test_boot_moment_is_a_recent_epoch():
    clock = SystemClock()
    assert 1_600_000_000 < clock.boot_epoch < 4_000_000_000


def test_readings_move_forward_and_use_the_zone():
    clock = SystemClock()
    first = clock.read(FixedOffsetZone())
    clock.wait_until(first.uptime + 0.02)
    second = clock.read(FixedOffsetZone())
    assert second.uptime > first.uptime
    assert abs((second.epoch - first.epoch) - (second.uptime - first.uptime)) < 1e-6
    assert second.local.utc_offset == -5 * 3600


def test_falls_back_to_the_hardware_clock():
    clock = SystemClock(stat_path="/nonexistent/stat")
    assert clock.boot_epoch > 1_600_000_000
