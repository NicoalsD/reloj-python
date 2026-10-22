from reloj.ui.menu import Menu, MenuOption, ask
from reloj.ui.themes import THEMES


def answers(*values):
    """Fake input() that returns the given answers and then behaves like Ctrl+D."""
    pending = list(values)

    def read(prompt):
        if not pending:
            raise EOFError
        return pending.pop(0)
    return read


def silent(*_):
    pass


def test_runs_the_chosen_option():
    calls = []
    menu = Menu([MenuOption("1", "Uno", lambda: calls.append(1))], read=answers("1"),
                write=silent)
    assert menu.show(THEMES[0]) is True
    assert calls == [1]


def test_zero_or_end_of_input_quits():
    assert Menu([], answers("0"), silent).show(THEMES[0]) is False
    assert Menu([], answers(), silent).show(THEMES[0]) is False


def test_enter_goes_back_to_the_clock():
    assert Menu([], answers(""), silent).show(THEMES[0]) is True


def test_ask_retries_until_valid_and_keeps_default_on_enter():
    assert ask("? ", int, 5, answers("x", "7"), silent) == 7
    assert ask("? ", int, 5, answers(""), silent) == 5
    assert ask("? ", int, 5, answers(), silent) == 5
