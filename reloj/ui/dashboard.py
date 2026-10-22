"""The main screen: analog clock on the left, digital clock and tools on the right.

The dashboard only reads the objects it receives; it never changes them.
"""

from reloj import config
from reloj.core.spanish import (format_clock, format_date, format_day_month, format_duration,
                                format_time, format_utc_offset, greeting, relative_day,
                                time_in_words)
from reloj.features.pomodoro import BREAK, IDLE
from reloj.ui.analog import draw_analog_clock
from reloj.ui.big_digits import big_text
from reloj.ui.canvas import BrailleCanvas
from reloj.ui.colors import hue_color, mix
from reloj.ui.screen import Screen
from reloj.ui.themes import Theme
from reloj.ui.widgets import draw_border, draw_row, progress_bar, section_title

TITLE = "Reloj en Python"
FOOTER = "Ctrl+C: menú · Python puro, cero librerías"
QUARTER_SYMBOLS = "◴◷◶◵"
POMODORO_BAR_WIDTH = 18

# Rows of the right panel.
DIGITS_ROW, DATE_ROW, GREETING_ROW, WORDS_ROW = 3, 9, 10, 11
WORLD_ROW, TOOLS_ROW = 13, 19


class Dashboard:
    def __init__(self):
        self.width, self.height = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        self.left, self.right = config.PANEL_LEFT, config.PANEL_RIGHT

    def palette(self, theme: Theme, reading, tools) -> Theme:
        """Theme for this frame: rainbow mode and a ringing alarm recolor the frame."""
        uptime = reading.uptime
        phase = tools.effects.rainbow_phase(uptime)
        if phase is not None:
            theme = theme.with_colors(frame=hue_color(phase))
        if tools.alarm.is_ringing(uptime) and int(uptime * 2) % 2 == 0:
            theme = theme.with_colors(frame=theme["accent"])
        return theme

    def render(self, reading, theme: Theme, tools) -> Screen:
        screen = Screen(self.width, self.height)
        draw_border(screen, TITLE, FOOTER)
        self._draw_analog(screen, reading, tools.effects)
        self._draw_digital(screen, reading, theme, tools.effects)
        self._draw_world(screen, reading, tools.world)
        section_title(screen, TOOLS_ROW, "Herramientas", self.left, self.right)
        self._draw_alarm(screen, TOOLS_ROW + 1, reading, tools.alarm)
        self._draw_stopwatch(screen, TOOLS_ROW + 2, reading, tools.stopwatch)
        self._draw_pomodoro(screen, TOOLS_ROW + 3, reading, tools.pomodoro)
        self._draw_countdown(screen, TOOLS_ROW + 4, reading, tools.countdown)
        if tools.alarm.is_ringing(reading.uptime):
            self._draw_alarm_banner(screen, reading, tools.alarm)
        return screen

    # Left side ---------------------------------------------------------------

    def _draw_analog(self, screen: Screen, reading, effects):
        canvas = BrailleCanvas(config.CLOCK_COLUMNS, config.CLOCK_ROWS)
        draw_analog_clock(canvas, reading.local.seconds_of_day, effects.direction,
                          effects.spin_angle(reading.uptime))
        if effects.reverse:
            screen.center(self.height - 2, "~ modo al revés ~", "muted",
                          config.CLOCK_LEFT, config.CLOCK_LEFT + config.CLOCK_COLUMNS)
        screen.draw_canvas(canvas, config.CLOCK_LEFT, config.CLOCK_TOP)

    # Right side --------------------------------------------------------------

    def _draw_digital(self, screen: Screen, reading, theme: Theme, effects):
        local = reading.local
        self._draw_big_time(screen, format_time(local), theme,
                            effects.rainbow_phase(reading.uptime))
        screen.center(DATE_ROW, format_date(local), "muted", self.left, self.right)
        screen.center(GREETING_ROW, "~ " + greeting(local.hour) + " ~", "highlight",
                      self.left, self.right)
        screen.center(WORDS_ROW, "« " + time_in_words(local.hour, local.minute) + " »", "ink",
                      self.left, self.right)

    def _draw_big_time(self, screen: Screen, content: str, theme: Theme,
                       rainbow: float | None):
        """Block digits with a vertical gradient, or a moving rainbow when 'rainbow' is a phase."""
        rows = big_text(content)
        x = self.left + (self.right - self.left - len(rows[0])) // 2
        for index, row in enumerate(rows):
            y = DIGITS_ROW + index
            if rainbow is None:
                screen.put(x, y, row, mix(theme["highlight"], theme["accent"], index / 4))
                continue
            for column, character in enumerate(row):
                screen.put(x + column, y, character,
                           hue_color((rainbow + column / 45.0 + index / 30.0) % 1.0))

    def _draw_world(self, screen: Screen, reading, world):
        section_title(screen, WORLD_ROW, "Relojes del mundo", self.left, self.right)
        for index, clock in enumerate(world):
            row = WORLD_ROW + 1 + index
            moment = clock.local_time(reading.epoch)
            if moment is None:
                screen.put(self.left + 2, row, clock.city + ": zona no disponible", "muted")
                continue
            screen.put(self.left + 2, row, QUARTER_SYMBOLS[moment.minute // 15], "accent")
            screen.put(self.left + 4, row, clock.city, "ink")
            screen.put(self.left + 17, row, format_time(moment), "highlight")
            screen.put(self.left + 28, row, format_utc_offset(moment.utc_offset), "muted")
            screen.put(self.left + 37, row, relative_day(moment.days, reading.local.days),
                       "muted")

    def _draw_alarm(self, screen: Screen, y: int, reading, alarm):
        if alarm.time is None:
            draw_row(screen, self.left, y, "Alarma", "--:--", "sin programar", "muted")
        elif alarm.is_ringing(reading.uptime):
            draw_row(screen, self.left, y, "Alarma", format_clock(alarm.time), "¡sonando!",
                     "accent")
        else:
            left = format_duration(alarm.seconds_left(reading.local))
            draw_row(screen, self.left, y, "Alarma", format_clock(alarm.time), "faltan " + left)

    def _draw_stopwatch(self, screen: Screen, y: int, reading, stopwatch):
        elapsed = stopwatch.elapsed(reading.uptime)
        value = "{:02d}:{:02d}.{}".format(int(elapsed) // 60, int(elapsed) % 60,
                                          int(elapsed * 10) % 10)
        if stopwatch.is_running:
            draw_row(screen, self.left, y, "Cronómetro", value, "en marcha", "accent")
        elif elapsed:
            draw_row(screen, self.left, y, "Cronómetro", value, "en pausa")
        else:
            draw_row(screen, self.left, y, "Cronómetro", value, "detenido", "muted")

    def _draw_pomodoro(self, screen: Screen, y: int, reading, pomodoro):
        phase = pomodoro.phase(reading.uptime)
        if phase == IDLE:
            draw_row(screen, self.left, y, "Pomodoro", _minutes(pomodoro.focus_seconds),
                     "listo para enfocarte", "muted")
        elif phase == BREAK:
            rest = "¡Descansa {} minutos!".format(int(pomodoro.break_seconds) // 60)
            draw_row(screen, self.left, y, "Pomodoro", "00:00", rest, "accent")
        else:
            bar = progress_bar(pomodoro.progress(reading.uptime), POMODORO_BAR_WIDTH)
            remaining = _minutes(pomodoro.remaining(reading.uptime))
            draw_row(screen, self.left, y, "Pomodoro", remaining)
            screen.put(self.left + 22, y, "▕" + bar + "▏", "accent")

    def _draw_countdown(self, screen: Screen, y: int, reading, countdown):
        title = format_day_month(countdown.day, countdown.month)
        if countdown.is_today(reading.local):
            draw_row(screen, self.left, y, "Cuenta atrás", "¡Hoy es el día!", title, "accent")
            return
        left = countdown.seconds_left(reading.local)
        value = "{}d {:02d}:{:02d}:{:02d}".format(left // 86400, left // 3600 % 24,
                                                 left // 60 % 60, left % 60)
        draw_row(screen, self.left, y, "Cuenta atrás", value, title)

    def _draw_alarm_banner(self, screen: Screen, reading, alarm):
        message = " ¡ALARMA! Son las {} · Ctrl+C para apagarla ".format(format_clock(alarm.time))
        flash = int(reading.uptime * 2) % 2 == 0
        screen.center(self.height - 2, message, "accent" if flash else "highlight")


def _minutes(seconds: float) -> str:
    """'MM:SS' for a countdown."""
    seconds = int(seconds)
    return "{:02d}:{:02d}".format(seconds // 60, seconds % 60)
