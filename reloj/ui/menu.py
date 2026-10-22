"""Menu opened with Ctrl+C, and the questions its options ask.

'read' and 'write' default to input() and print() but can be replaced, which keeps
the menu testable.
"""

from reloj.ui.colors import RESET, foreground
from reloj.ui.terminal import CLEAR
from reloj.ui.themes import Theme

QUIT_KEY = "0"
LABEL_WIDTH = 43


class MenuOption:
    __slots__ = ("key", "label", "action")

    def __init__(self, key: str, label: str, action):
        self.key, self.label, self.action = key, label, action


class Menu:
    def __init__(self, options: list[MenuOption], read=input, write=print):
        self.options = options
        self._read = read
        self._write = write

    def show(self, theme: Theme) -> bool:
        """Print the options and run the chosen one; False means the user wants to quit."""
        self._print(theme)
        try:
            choice = self._read("  Opción: ").strip()
        except (EOFError, KeyboardInterrupt):
            return False
        if choice == QUIT_KEY:
            return False
        for option in self.options:
            if option.key == choice:
                try:
                    option.action()
                except KeyboardInterrupt:   # Ctrl+C inside a question just cancels it
                    pass
        return True

    def _print(self, theme: Theme):
        frame, title, muted = (foreground(theme["frame"]), foreground(theme["highlight"]),
                               foreground(theme["muted"]))
        self._write(CLEAR + "{}╭──────────────── {}Menú del reloj{} ────────────────╮".format(
            frame, title, frame))
        rows = [(option.key, option.label) for option in self.options] + [(QUIT_KEY, "Salir")]
        for key, label in rows:
            line = "{}│{}  {}{}{}  {:<{width}}{}│"
            self._write(line.format(frame, RESET, title, key, RESET, label, frame,
                                    width=LABEL_WIDTH))
        self._write("╰" + "─" * (LABEL_WIDTH + 5) + "╯" + RESET)
        self._write(muted + "  Enter vuelve al reloj." + RESET)


def ask(question: str, parse, default, read=input, write=print):
    """Keep asking until 'parse' accepts the answer; Enter (or end of input) keeps the default."""
    while True:
        try:
            answer = read(question).strip()
        except EOFError:
            write()
            return default
        if not answer:
            return default
        try:
            return parse(answer)
        except ValueError:
            write("  Valor no válido, intenta de nuevo.")


def print_choices(choices: list[tuple[str, tuple[int, int, int]]], write=print):
    """Numbered list, each entry in its own color."""
    for index, (name, rgb) in enumerate(choices):
        write("   {}{}) {}{}".format(foreground(rgb), index + 1, name, RESET))
