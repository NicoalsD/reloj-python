"""Application: owns the state, runs the live loop and opens the menu on Ctrl+C."""

from reloj import config
from reloj.core.parsing import parse_choice, parse_clock_time, parse_day_month
from reloj.core.system_clock import SystemClock
from reloj.core.timezones import TimeZone
from reloj.features.countdown import Countdown
from reloj.features.toolbox import Toolbox
from reloj.features.world import load_world_clocks
from reloj.ui.dashboard import Dashboard
from reloj.ui.menu import Menu, MenuOption, ask, print_choices
from reloj.ui.terminal import Terminal
from reloj.ui.themes import THEMES, Theme


class ClockApp:
    def __init__(self):
        self.clock = SystemClock()
        self.zone = TimeZone.local()
        self.tools = Toolbox(load_world_clocks())
        self.theme_index = 0
        self.dashboard = Dashboard()
        self.terminal = Terminal()
        self.menu = Menu(self._menu_options())
        self.reading = self.clock.read(self.zone)
        self._last_bell_second = -1

    @property
    def theme(self) -> Theme:
        return THEMES[self.theme_index]

    def run(self):
        """Alternate between the live clock and the menu until the user quits."""
        while True:
            self._run_clock()
            if self.tools.alarm.is_ringing(self.reading.uptime):
                self.tools.alarm.silence()   # Ctrl+C while ringing only silences it
                continue
            if not self.menu.show(self.theme):
                break
        print("\n¡Hasta luego! 👋")

    # Live clock --------------------------------------------------------------

    def _run_clock(self):
        """Redraw in place several times per second until Ctrl+C."""
        frame_seconds = 1.0 / config.FRAMES_PER_SECOND
        self.terminal.enter()
        try:
            next_frame = self.clock.uptime()
            while True:
                self._draw_frame()
                next_frame = max(next_frame + frame_seconds, self.reading.uptime)
                self.clock.wait_until(next_frame)
        except KeyboardInterrupt:
            pass
        finally:
            self.terminal.leave()

    def _draw_frame(self):
        self.reading = self.clock.read(self.zone)
        uptime = self.reading.uptime
        self.tools.update(self.reading.local, uptime)
        bell = self.tools.wants_bell(uptime) and self._new_bell_second(uptime)
        screen = self.dashboard.render(self.reading, self.theme, self.tools)
        palette = self.dashboard.palette(self.theme, self.reading, self.tools)
        self.terminal.draw(screen.render(palette), bell)

    def _new_bell_second(self, uptime: float) -> bool:
        """Ring at most once per second."""
        if int(uptime) == self._last_bell_second:
            return False
        self._last_bell_second = int(uptime)
        return True

    # Menu --------------------------------------------------------------------

    def _menu_options(self) -> list[MenuOption]:
        tools = self.tools
        return [
            MenuOption("1", "Cambiar tema", self._choose_theme),
            MenuOption("2", "Programar o quitar la alarma", self._choose_alarm),
            MenuOption("3", "Cronómetro: iniciar o pausar",
                       lambda: tools.stopwatch.toggle(self.clock.uptime())),
            MenuOption("4", "Cronómetro: reiniciar", tools.stopwatch.reset),
            MenuOption("5", "Pomodoro ({} min): iniciar o cancelar".format(
                config.POMODORO_FOCUS_SECONDS // 60),
                       lambda: tools.pomodoro.toggle(self.clock.uptime())),
            MenuOption("6", "Cambiar la fecha de la cuenta atrás", self._choose_countdown),
            MenuOption("7", "Reloj al revés: activar o desactivar", tools.effects.toggle_reverse),
            MenuOption("8", "¡Girar el reloj!", lambda: tools.effects.spin(self.clock.uptime())),
            MenuOption("9", "Modo arcoíris: activar o desactivar", tools.effects.toggle_rainbow),
        ]

    def _choose_theme(self):
        print_choices([(theme.name, theme["accent"]) for theme in THEMES])
        self.theme_index = ask("  Tema: ", lambda answer: parse_choice(answer, len(THEMES)),
                               self.theme_index)

    def _choose_alarm(self):
        self.tools.alarm.set(ask("  Hora de la alarma (HH:MM, Enter para quitarla): ",
                                 parse_clock_time, None))

    def _choose_countdown(self):
        day, month = ask("  Fecha para la cuenta atrás (DD/MM, Enter para Navidad): ",
                         parse_day_month, config.DEFAULT_COUNTDOWN)
        self.tools.countdown = Countdown(day, month)
