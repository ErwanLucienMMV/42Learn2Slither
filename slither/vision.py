"""The interpreter's visible state, restricted to four rays from the head."""

from dataclasses import dataclass

from slither.environment import Action, SnakeGame


@dataclass(frozen=True)
class Vision:
    """Each ray lists cells nearest-first, including the wall at its end.

    Objects do not hide cells behind them, matching the subject's diagram.
    A zero-length terminal snake has four empty rays.
    """

    up: tuple[str, ...]
    left: tuple[str, ...]
    down: tuple[str, ...]
    right: tuple[str, ...]

    def as_text(self) -> str:
        """Render the visible cross using W, H, S, G, R and 0."""
        if not self.up:
            return "Snake has no remaining cells."
        indent = " " * len(self.left)
        lines = [indent + cell for cell in reversed(self.up)]
        lines.append("".join(reversed(self.left)) + "H" + "".join(self.right))
        lines.extend(indent + cell for cell in self.down)
        return "\n".join(lines)


def observe(game: SnakeGame) -> Vision:
    """Extract vision for a future agent; do not pass the board to it."""
    if not game.snake:
        return Vision((), (), (), ())
    body = set(game.snake[1:])
    greens = game.green_apples
    rays = []
    for action in Action:
        x, y = game.snake[0]
        dx, dy = action.delta
        ray = []
        while True:
            x, y = x + dx, y + dy
            cell = (x, y)
            if not game.contains(cell):
                ray.append("W")
                break
            if cell in body:
                ray.append("S")
            elif cell in greens:
                ray.append("G")
            elif cell == game.red_apple:
                ray.append("R")
            else:
                ray.append("0")
        rays.append(tuple(ray))
    return Vision(*rays)
