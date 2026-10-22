"""Validation of what the user types in the menu; every parser raises ValueError."""

from reloj.core.dates import days_in_month

LEAP_YEAR = 2024   # lets 29/02 be chosen as a countdown date


def parse_clock_time(answer: str) -> int:
    """'7:30' or '07:30' -> seconds since midnight."""
    hours, minutes = (int(part) for part in answer.split(":"))
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        raise ValueError(answer)
    return hours * 3600 + minutes * 60


def parse_day_month(answer: str) -> tuple[int, int]:
    """'24/12' -> (24, 12)."""
    day, month = (int(part) for part in answer.split("/"))
    if not (1 <= month <= 12 and 1 <= day <= days_in_month(LEAP_YEAR, month)):
        raise ValueError(answer)
    return day, month


def parse_choice(answer: str, count: int) -> int:
    """'1'..'count' -> zero based index."""
    index = int(answer) - 1
    if not 0 <= index < count:
        raise ValueError(answer)
    return index
