"""Terminal control through escape sequences."""

from reloj.ui.colors import ESCAPE

ENTER_SCREEN = ESCAPE + "?1049h" + ESCAPE + "?25l"   # alternate screen, hidden cursor
LEAVE_SCREEN = ESCAPE + "?25h" + ESCAPE + "?1049l"
HOME = ESCAPE + "H"
CLEAR = ESCAPE + "2J" + HOME
BELL = "\a"


class Terminal:
    def enter(self):
        """Switch to a clean screen so the user's scrollback is left untouched."""
        print(ENTER_SCREEN, end="")

    def leave(self):
        try:
            print(LEAVE_SCREEN, end="", flush=True)
        except KeyboardInterrupt:   # a second Ctrl+C must still restore the terminal
            print(LEAVE_SCREEN, end="", flush=True)

    def draw(self, frame: str, bell: bool = False):
        """Redraw in place from the top-left corner."""
        print(HOME + frame + (BELL if bell else ""), end="", flush=True)

    def clear(self):
        print(CLEAR, end="")
