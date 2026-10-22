"""Tiny test runner without unittest or pytest: python3 -m tests"""

from tests import (test_alarm, test_canvas, test_colors, test_countdown, test_dates,
                   test_effects, test_parsing, test_pomodoro, test_spanish, test_stopwatch,
                   test_system_clock, test_themes, test_timezones, test_toolbox, test_trig,
                   test_world)

TEST_MODULES = [
    test_alarm,
    test_canvas,
    test_colors,
    test_countdown,
    test_dates,
    test_effects,
    test_parsing,
    test_pomodoro,
    test_spanish,
    test_stopwatch,
    test_system_clock,
    test_themes,
    test_timezones,
    test_toolbox,
    test_trig,
    test_world,
]


def run(modules) -> list[str]:
    """Run every test_* function and return the descriptions of the failures."""
    failures = []
    total = 0
    for module in modules:
        for name, test in vars(module).items():
            if not (name.startswith("test_") and callable(test)):
                continue
            total += 1
            try:
                test()
            except Exception as error:
                failures.append("{}.{}: {!r}".format(module.__name__, name, error))
    print("{} pruebas, {} fallidas".format(total, len(failures)))
    return failures


def main():
    failures = run(TEST_MODULES)
    for failure in failures:
        print("  FALLÓ", failure)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
