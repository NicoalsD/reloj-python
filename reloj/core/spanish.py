"""Spanish names and formats shown to the user."""

from reloj.core.dates import LocalTime

DAY_NAMES = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]
MONTH_NAMES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
               "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
HOUR_WORDS = ["doce", "una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
              "nueve", "diez", "once"]
NUMBER_WORDS = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
                "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete",
                "dieciocho", "diecinueve", "veinte", "veintiuno", "veintidós", "veintitrés",
                "veinticuatro", "veinticinco", "veintiséis", "veintisiete", "veintiocho",
                "veintinueve"]


def format_date(moment: LocalTime) -> str:
    """Long date such as 'Miércoles, 21 de octubre de 2026'."""
    text = "{}, {} de {} de {}".format(DAY_NAMES[moment.weekday], moment.day,
                                      MONTH_NAMES[moment.month - 1], moment.year)
    return text[0].upper() + text[1:]


def format_day_month(day: int, month: int) -> str:
    return "{} de {}".format(day, MONTH_NAMES[month - 1])


def format_time(moment: LocalTime) -> str:
    return "{:02d}:{:02d}:{:02d}".format(moment.hour, moment.minute, moment.second)


def format_clock(seconds_of_day: float) -> str:
    """'HH:MM' for a number of seconds since midnight."""
    seconds = int(seconds_of_day)
    return "{:02d}:{:02d}".format(seconds // 3600, seconds // 60 % 60)


def format_duration(seconds: float) -> str:
    """Rough remaining time: '9 h 05 min' or '4 min 30 s'."""
    seconds = int(seconds)
    hours, minutes = seconds // 3600, seconds // 60 % 60
    if hours:
        return "{} h {:02d} min".format(hours, minutes)
    return "{} min {:02d} s".format(minutes, seconds % 60)


def format_utc_offset(offset: int) -> str:
    sign = "+" if offset >= 0 else "-"
    hours, minutes = abs(offset) // 3600, abs(offset) // 60 % 60
    return "UTC{}{}{}".format(sign, hours, ":{:02d}".format(minutes) if minutes else "")


def relative_day(days: int, home_days: int) -> str:
    return {-1: "ayer", 0: "hoy", 1: "mañana"}.get(days - home_days, "")


def greeting(hour: int) -> str:
    if hour < 6:
        return "¡A dormir, búho nocturno!"
    if hour < 12:
        return "¡Buenos días!"
    if hour < 14:
        return "¡Hora de almorzar!"
    if hour < 19:
        return "¡Buenas tardes!"
    return "¡Buenas noches!"


def time_in_words(hour: int, minute: int) -> str:
    """Spoken time: 'Son las tres y cuarto', 'Es la una menos diez'."""
    if minute <= 30:
        target = hour % 12
        special = {0: "en punto", 15: "y cuarto", 30: "y media"}
        tail = special[minute] if minute in special else "y " + NUMBER_WORDS[minute]
    else:
        target = (hour + 1) % 12
        tail = "menos cuarto" if minute == 45 else "menos " + NUMBER_WORDS[60 - minute]
    start = "Es la una" if target == 1 else "Son las " + HOUR_WORDS[target]
    return start + " " + tail
