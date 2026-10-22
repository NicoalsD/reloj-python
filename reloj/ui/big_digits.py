"""Big block digits, five rows tall."""

FONT = {
    "0": ["█████", "█   █", "█   █", "█   █", "█████"],
    "1": ["  █  ", " ██  ", "  █  ", "  █  ", " ███ "],
    "2": ["█████", "    █", "█████", "█    ", "█████"],
    "3": ["█████", "    █", " ████", "    █", "█████"],
    "4": ["█   █", "█   █", "█████", "    █", "    █"],
    "5": ["█████", "█    ", "█████", "    █", "█████"],
    "6": ["█████", "█    ", "█████", "█   █", "█████"],
    "7": ["█████", "    █", "   █ ", "  █  ", "  █  "],
    "8": ["█████", "█   █", "█████", "█   █", "█████"],
    "9": ["█████", "█   █", "█████", "    █", "█████"],
    ":": ["   ", " ▀ ", "   ", " ▀ ", "   "],
    " ": ["   ", "   ", "   ", "   ", "   "],
}
FONT_HEIGHT = 5


def big_text(content: str) -> list[str]:
    """Rows of 'content' written with the big font, one space between characters."""
    return [" ".join(FONT[character][row] for character in content)
            for row in range(FONT_HEIGHT)]
