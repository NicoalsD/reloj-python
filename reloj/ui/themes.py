"""Color themes. Every drawing refers to a role name, never to a fixed color.

Roles: bg (background), ink (main text), accent, muted (secondary text),
highlight and frame (borders and dial rim).
"""

from reloj.ui.colors import RGB


class Theme:
    def __init__(self, name: str, **colors: RGB):
        self.name = name
        self.colors = colors

    def __getitem__(self, role: str) -> RGB:
        return self.colors[role]

    def with_colors(self, **overrides: RGB) -> "Theme":
        """Copy of the theme with some roles changed (used by the flashing effects)."""
        return Theme(self.name, **dict(self.colors, **overrides))


THEMES = [
    Theme("Medianoche", bg=(15, 17, 35), ink=(226, 232, 255), accent=(255, 94, 98),
          muted=(110, 118, 160), highlight=(138, 180, 255), frame=(70, 80, 140)),
    Theme("Clásico", bg=(244, 247, 251), ink=(31, 42, 90), accent=(232, 64, 42),
          muted=(138, 144, 166), highlight=(142, 43, 143), frame=(31, 42, 90)),
    Theme("Neón", bg=(13, 2, 33), ink=(244, 241, 255), accent=(255, 42, 109),
          muted=(157, 143, 214), highlight=(5, 217, 232), frame=(255, 42, 109)),
    Theme("Matrix", bg=(0, 0, 0), ink=(57, 255, 20), accent=(198, 255, 0),
          muted=(31, 143, 58), highlight=(0, 255, 156), frame=(20, 110, 40)),
    Theme("Atardecer", bg=(45, 20, 44), ink=(255, 236, 214), accent=(255, 107, 53),
          muted=(181, 131, 141), highlight=(255, 183, 3), frame=(230, 57, 70)),
]
