"""Display-independent rules for the Learn2Slither board."""

from dataclasses import dataclass
from enum import Enum
from random import Random

Cell = tuple[int, int]


class Action(str, Enum):
    """Absolute moves, in the subject's order."""

    UP = "UP"
    LEFT = "LEFT"
    DOWN = "DOWN"
    RIGHT = "RIGHT"

    @property
    def delta(self) -> Cell:
        return {
            Action.UP: (0, -1),
            Action.LEFT: (-1, 0),
            Action.DOWN: (0, 1),
            Action.RIGHT: (1, 0),
        }[self]


class Event(str, Enum):
    MOVED = "moved"
    GREEN_APPLE = "green_apple"
    RED_APPLE = "red_apple"
    WALL_COLLISION = "wall_collision"
    BODY_COLLISION = "body_collision"
    ZERO_LENGTH = "zero_length"
    BOARD_COMPLETE = "board_complete"


@dataclass(frozen=True)
class StepResult:
    """Facts about a move; reward values belong in a future interpreter."""

    action: Action
    event: Event
    terminated: bool
    length: int
    steps: int


class SnakeGame:
    """A 10x10 board. Coordinates are (x, y), with y growing downward.

    Each turn_* method performs exactly one move. Reverse moves are accepted
    and collide with the body when the destination is occupied.
    """

    size = 10

    def __init__(self, seed: int | None = None) -> None:
        self._random = Random(seed)
        self.reset()

    @property
    def snake(self) -> tuple[Cell, ...]:
        """The head first, followed by the body toward the tail."""
        return self._snake

    @property
    def green_apples(self) -> frozenset[Cell]:
        return frozenset(self._green_apples)

    @property
    def red_apple(self) -> Cell | None:
        return self._red_apple

    def reset(self, seed: int | None = None) -> None:
        """Start a new round; an explicit seed restarts the random sequence."""
        if seed is not None:
            self._random.seed(seed)
        self.direction = self._random.choice(tuple(Action))
        dx, dy = self.direction.delta
        starts = [
            (x, y)
            for y in range(self.size)
            for x in range(self.size)
            if self.contains((x - 2 * dx, y - 2 * dy))
        ]
        x, y = self._random.choice(starts)
        self._snake = tuple((x - i * dx, y - i * dy) for i in range(3))
        self._green_apples: set[Cell] = set()
        self._red_apple: Cell | None = None
        for _ in range(2):
            self._green_apples.add(self._free_cell())
        self._red_apple = self._free_cell()
        self.steps = 0
        self.max_length = 3
        self.green_eaten = 0
        self.red_eaten = 0
        self.terminated = False
        self.end_reason: Event | None = None

    def contains(self, cell: Cell) -> bool:
        x, y = cell
        return 0 <= x < self.size and 0 <= y < self.size

    def _free_cell(self) -> Cell | None:
        occupied = set(self._snake) | self._green_apples
        occupied.add(self._red_apple)
        free = [
            (x, y)
            for y in range(self.size)
            for x in range(self.size)
            if (x, y) not in occupied
        ]
        return self._random.choice(free) if free else None

    def turn_up(self) -> StepResult:
        """Move one cell toward the top of the board."""
        return self.step(Action.UP)

    def turn_left(self) -> StepResult:
        """Move one cell toward the left of the board."""
        return self.step(Action.LEFT)

    def turn_down(self) -> StepResult:
        """Move one cell toward the bottom of the board."""
        return self.step(Action.DOWN)

    def turn_right(self) -> StepResult:
        """Move one cell toward the right of the board."""
        return self.step(Action.RIGHT)

    def step(self, action: Action | str) -> StepResult:
        """Apply one absolute action and return its outcome without a reward.

        Every currently occupied body cell is a collision, including the tail.
        A finished round must be reset before another action can be applied.
        """
        action = Action(action)
        if self.terminated:
            raise RuntimeError("Round finished; call reset() before moving.")
        self.direction = action
        self.steps += 1
        x, y = self._snake[0]
        dx, dy = action.delta
        destination = (x + dx, y + dy)
        if not self.contains(destination):
            return self._finish(action, Event.WALL_COLLISION)
        if destination in self._snake:
            return self._finish(action, Event.BODY_COLLISION)

        event = Event.MOVED
        length = len(self._snake)
        if destination in self._green_apples:
            self._green_apples.remove(destination)
            self.green_eaten += 1
            length += 1
            event = Event.GREEN_APPLE
        elif destination == self._red_apple:
            self._red_apple = None
            self.red_eaten += 1
            length -= 1
            event = Event.RED_APPLE
        self._snake = (destination, *self._snake)[:length]
        self.max_length = max(self.max_length, length)
        if not length:
            return self._finish(action, Event.ZERO_LENGTH)
        if length == self.size * self.size:
            return self._finish(action, Event.BOARD_COMPLETE)
        self._replenish_apples()
        if not self._green_apples:
            return self._finish(action, Event.BOARD_COMPLETE)
        return self._result(action, event)

    def _replenish_apples(self) -> None:
        """Restore missing apples when space permits, also after shrink."""
        if self._red_apple is None:
            self._red_apple = self._free_cell()
        while len(self._green_apples) < 2:
            replacement = self._free_cell()
            if replacement is None:
                break
            self._green_apples.add(replacement)

    def _finish(self, action: Action, event: Event) -> StepResult:
        self.terminated = True
        self.end_reason = event
        return self._result(action, event)

    def _result(self, action: Action, event: Event) -> StepResult:
        return StepResult(
            action, event, self.terminated, len(self._snake), self.steps,
        )
