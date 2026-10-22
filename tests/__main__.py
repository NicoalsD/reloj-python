"""Tiny test runner without unittest or pytest: python3 -m tests"""

from tests import (test_alarm, test_dates, test_parsing, test_spanish, test_system_clock,
                   test_timezones, test_trig)

TEST_MODULES = [
    test_alarm,
    test_dates,
    test_parsing,
    test_spanish,
    test_system_clock,
    test_timezones,
    test_trig,
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
