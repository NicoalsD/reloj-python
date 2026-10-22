"""Braille canvas: every terminal cell holds a 2 x 4 grid of dots."""

from reloj.core.trig import polar

BRAILLE_BASE = 0x2800
BRAILLE_BITS = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]


class BrailleCanvas:
    """Dot canvas with square pixels, because a cell is twice as tall as it is wide.

    Colors are theme role names or RGB tuples; each cell keeps the last color drawn on it.
    """

    def __init__(self, columns: int, rows: int):
        self.columns, self.rows = columns, rows
        self.width, self.height = columns * 2, rows * 4
        self._bits = [[0] * columns for _ in range(rows)]
        self._colors = [[None] * columns for _ in range(rows)]
        self._labels = {}

    def dot(self, x: float, y: float, color):
        x, y = int(x + 0.5), int(y + 0.5)
        if 0 <= x < self.width and 0 <= y < self.height:
            row, column = y // 4, x // 2
            self._bits[row][column] |= BRAILLE_BITS[y % 4][x % 2]
            self._colors[row][column] = color

    def line(self, x1: float, y1: float, x2: float, y2: float, color, thickness: float = 0.0):
        """Straight line; 'thickness' adds parallel lines on both sides."""
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 or 1.0
        normal_x, normal_y = -(y2 - y1) / length, (x2 - x1) / length
        steps = int(length * 2) + 1
        shift = -thickness
        while shift <= thickness:
            for step in range(steps + 1):
                ratio = step / steps
                self.dot(x1 + (x2 - x1) * ratio + normal_x * shift,
                         y1 + (y2 - y1) * ratio + normal_y * shift, color)
            shift += 0.5

    def circle(self, cx: float, cy: float, radius: float, color):
        steps = int(radius * 8) + 8
        for step in range(steps):
            self.dot(*polar(cx, cy, radius, 360.0 * step / steps), color=color)

    def label(self, x: float, y: float, content: str, color):
        """Plain text placed over the dots, centered on the pixel (x, y)."""
        row, column = int(y) // 4, int(x) // 2 - len(content) // 2
        for index, character in enumerate(content):
            self._labels[(row, column + index)] = (character, color)

    def cells(self):
        """Yield (row, column, character, color) for every cell."""
        for row in range(self.rows):
            for column in range(self.columns):
                if (row, column) in self._labels:
                    yield (row, column) + self._labels[(row, column)]
                elif self._bits[row][column]:
                    yield (row, column, chr(BRAILLE_BASE + self._bits[row][column]),
                           self._colors[row][column])
                else:
                    yield row, column, " ", None
