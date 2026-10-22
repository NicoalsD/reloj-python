"""Character grid that becomes one ANSI frame."""

from reloj.ui.colors import RESET, background, foreground


class Screen:
    """Colors are theme role names or RGB tuples; empty cells use the 'ink' role."""

    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self._chars = [[" "] * width for _ in range(height)]
        self._colors = [[None] * width for _ in range(height)]

    def put(self, x: int, y: int, content: str, color=None):
        for index, character in enumerate(content):
            if 0 <= x + index < self.width and 0 <= y < self.height:
                self._chars[y][x + index] = character
                self._colors[y][x + index] = color

    def center(self, y: int, content: str, color=None, left: int = 0, right: int | None = None):
        right = self.width if right is None else right
        self.put(left + (right - left - len(content)) // 2, y, content, color)

    def draw_canvas(self, canvas, x: int, y: int):
        for row, column, character, color in canvas.cells():
            self.put(x + column, y + row, character, color)

    def text(self) -> str:
        """Plain characters without colors (handy for tests)."""
        return "\n".join("".join(row) for row in self._chars)

    def render(self, theme) -> str:
        """Whole frame, emitting a color code only when the color changes."""
        lines = []
        for y in range(self.height):
            parts, current = [background(theme["bg"])], None
            for x in range(self.width):
                color = self._colors[y][x] or "ink"
                rgb = theme[color] if isinstance(color, str) else color
                if rgb != current:
                    parts.append(foreground(rgb))
                    current = rgb
                parts.append(self._chars[y][x])
            lines.append("".join(parts) + RESET)
        return "\n".join(lines)
