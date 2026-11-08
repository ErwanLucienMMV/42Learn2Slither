"""Manual controls and graphical rendering; no policy or learning code."""

import pygame

from slither.environment import Action, Event, SnakeGame
from slither.vision import observe

BACKGROUND = (14, 21, 34)
PANEL = (23, 33, 50)
TEXT = (232, 239, 249)
MUTED = (149, 167, 190)
BLUE = (67, 133, 237)
HEAD = (109, 181, 255)
GREEN = (100, 219, 148)
RED = (249, 111, 123)
GOLD = (250, 207, 106)
CELL_SIZE = 52
BOARD_ORIGIN = (28, 116)

KEY_ACTIONS = {
    pygame.K_UP: Action.UP, pygame.K_w: Action.UP,
    pygame.K_LEFT: Action.LEFT, pygame.K_a: Action.LEFT,
    pygame.K_DOWN: Action.DOWN, pygame.K_s: Action.DOWN,
    pygame.K_RIGHT: Action.RIGHT, pygame.K_d: Action.RIGHT,
}

END_LABELS = {
    Event.WALL_COLLISION: "You hit a wall.",
    Event.BODY_COLLISION: "You hit the snake's body.",
    Event.ZERO_LENGTH: "No cells left after that red apple.",
    Event.BOARD_COMPLETE: "All 100 cells belong to the snake.",
}


class GameWindow:
    def __init__(
        self, seed: int | None = None, speed: float = 5,
        step_mode: bool = False, quiet: bool = False,
    ) -> None:
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((908, 718))
        pygame.display.set_caption("Learn2Slither | Snake")
        self.fonts = {
            "small": pygame.font.Font(None, 22),
            "body": pygame.font.Font(None, 27),
            "title": pygame.font.Font(None, 42),
            "number": pygame.font.Font(None, 60),
        }
        self.game = SnakeGame(seed)
        self.speed = speed
        self.step_mode = step_mode
        self.quiet = quiet
        self.paused = True
        self.pending_action = self.game.direction
        self.running = True
        self.round_number = 1
        self.next_move = 0.0
        self.buttons = {
            "pause": pygame.Rect(576, 357, 304, 42),
            "step": pygame.Rect(576, 409, 304, 42),
            "restart": pygame.Rect(576, 461, 304, 42),
        }

    def run(self) -> None:
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            if not self.running:
                break
            now = pygame.time.get_ticks()
            if (
                not self.paused and not self.step_mode
                and not self.game.terminated and now >= self.next_move
            ):
                self.move()
            self.draw()
            pygame.display.flip()
            clock.tick(60)

    def move(self) -> None:
        if self.game.terminated:
            return
        if not self.quiet:
            print(observe(self.game).as_text())
            print(self.pending_action.value, flush=True)
        result = self.game.step(self.pending_action)
        self.next_move = pygame.time.get_ticks() + 1000 / self.speed
        if result.terminated:
            self.paused = True
            if not self.quiet:
                print(
                    f"{END_LABELS[result.event]} "
                    f"Length {result.length}, max {self.game.max_length}, "
                    f"moves {result.steps}.", flush=True,
                )

    def restart(self) -> None:
        self.game.reset()
        self.round_number += 1
        self.pending_action = self.game.direction
        self.paused = True
        self.next_move = 0

    def toggle_pause(self) -> None:
        if self.step_mode:
            self.single_step()
            return
        if not self.game.terminated:
            self.paused = not self.paused
            self.next_move = pygame.time.get_ticks() + 1000 / self.speed

    def single_step(self) -> None:
        self.paused = True
        self.move()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            callbacks = {
                "pause": self.toggle_pause,
                "step": self.single_step,
                "restart": self.restart,
            }
            for name, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    callbacks[name]()
        elif event.type == pygame.KEYDOWN:
            self._handle_key(event.key)

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_r:
            self.restart()
        elif key == pygame.K_TAB:
            self.step_mode = not self.step_mode
            self.paused = True
        elif key == pygame.K_SPACE:
            if self.step_mode:
                self.move()
            else:
                self.toggle_pause()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.single_step()
        elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.speed = min(30, self.speed + 1)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.speed = max(1, self.speed - 1)
        elif key in KEY_ACTIONS and not self.game.terminated:
            self.pending_action = KEY_ACTIONS[key]
            if self.step_mode:
                self.move()

    def text(
        self, value: str, position: tuple[int, int],
        style: str = "body", color: tuple = TEXT,
    ) -> None:
        glyph = self.fonts[style].render(value, True, color)
        self.screen.blit(glyph, position)

    def cell_rect(self, cell: tuple[int, int]) -> pygame.Rect:
        x, y = cell
        return pygame.Rect(
            BOARD_ORIGIN[0] + x * CELL_SIZE,
            BOARD_ORIGIN[1] + y * CELL_SIZE, CELL_SIZE, CELL_SIZE,
        )

    def draw(self) -> None:
        self.screen.fill(BACKGROUND)
        self.text("Learn2Slither", (28, 25), "title")
        self.text("Two green apples. One red. Every move counts.",
                  (29, 72), color=MUTED)
        self.text(f"ROUND {self.round_number:02}", (753, 35), color=MUTED)
        self._draw_board()
        self._draw_panel()
        self.text("G  grow +1", (28, 656), color=GREEN)
        self.text("R  shrink -1", (184, 656), color=RED)
        self.text("Blue is you. Fill the board to win.",
                  (28, 687), "small", MUTED)
        if self.game.terminated:
            self._draw_end_screen()

    def _draw_board(self) -> None:
        for y in range(self.game.size):
            for x in range(self.game.size):
                color = (27, 39, 57) if (x + y) % 2 else (30, 43, 61)
                pygame.draw.rect(self.screen, color, self.cell_rect((x, y)))
        for apple in self.game.green_apples:
            self._draw_apple(apple, GREEN, "G")
        if self.game.red_apple is not None:
            self._draw_apple(self.game.red_apple, RED, "R")
        for index, cell in enumerate(self.game.snake):
            rect = self.cell_rect(cell).inflate(-4, -4)
            pygame.draw.rect(
                self.screen, HEAD if index == 0 else BLUE, rect,
                border_radius=8,
            )
        if self.game.snake:
            self._draw_eyes()
        border = pygame.Rect(*BOARD_ORIGIN, 520, 520)
        pygame.draw.rect(self.screen, (59, 77, 100), border, 1)

    def _draw_apple(self, cell: tuple[int, int], color: tuple, label: str):
        rect = self.cell_rect(cell)
        pygame.draw.circle(self.screen, color, rect.center, 17)
        glyph = self.fonts["small"].render(label, True, BACKGROUND)
        self.screen.blit(glyph, glyph.get_rect(center=rect.center))
        stem = (rect.centerx + 3, rect.centery - 20)
        pygame.draw.line(self.screen, color, stem,
                         (stem[0] + 5, stem[1] - 3), 3)

    def _draw_eyes(self) -> None:
        rect = self.cell_rect(self.game.snake[0])
        dx, dy = self.game.direction.delta
        for side in (-1, 1):
            center = (
                rect.centerx + dx * 10 + dy * 8 * side,
                rect.centery + dy * 10 + dx * 8 * side,
            )
            pygame.draw.circle(self.screen, BACKGROUND, center, 4)

    def _draw_panel(self) -> None:
        pygame.draw.rect(self.screen, PANEL, (576, 116, 304, 219),
                         border_radius=12)
        self.text("LENGTH", (596, 134), "small", MUTED)
        self.text(str(len(self.game.snake)), (594, 160), "number")
        self.text("/ 100", (680, 185), color=MUTED)
        self.text(f"Best this round   {self.game.max_length}", (596, 226))
        self.text(f"Moves   {self.game.steps}", (596, 260), color=MUTED)
        eaten = f"Eaten    G {self.game.green_eaten}   R {self.game.red_eaten}"
        self.text(eaten, (596, 294), "small", MUTED)
        labels = {
            "pause": (
                "Resume  [Space]" if self.paused else "Pause  [Space]"
            ),
            "step": "Next move  [Enter]",
            "restart": "New round  [R]",
        }
        if self.step_mode:
            labels["pause"] = "Next move  [Space]"
        if self.game.terminated:
            labels["pause"] = "Round finished"
        mouse = pygame.mouse.get_pos()
        for name, rect in self.buttons.items():
            color = (43, 62, 87) if rect.collidepoint(mouse) else PANEL
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            self.text(labels[name], (rect.x + 18, rect.y + 10))
        mode = "STEP MODE" if self.step_mode else "REAL TIME"
        state = "PAUSED" if self.paused else "PLAYING"
        self.text(f"{mode} / {state}", (576, 530), "small", GREEN)
        self.text(f"Speed  {self.speed:g} moves/s   [- / +]",
                  (576, 560), "small", MUTED)
        self.text("Arrows / WASD   choose direction",
                  (576, 594), "small", MUTED)
        self.text("Tab   switch step / real time", (576, 621), "small", MUTED)
        self.text(f"Next   {self.pending_action.value}", (576, 662))
        self.text("Esc   quit", (576, 690), "small", MUTED)

    def _draw_end_screen(self) -> None:
        shade = pygame.Surface((520, 520), pygame.SRCALPHA)
        shade.fill((8, 14, 26, 195))
        self.screen.blit(shade, BOARD_ORIGIN)
        won = self.game.end_reason == Event.BOARD_COMPLETE
        card = pygame.Rect(72, 266, 432, 186)
        pygame.draw.rect(self.screen, PANEL, card, border_radius=12)
        pygame.draw.rect(self.screen, GOLD if won else BLUE, card, 1,
                         border_radius=12)
        lines = (
            ("YOU WIN" if won else "ROUND OVER", "title", 306,
             GOLD if won else TEXT),
            (END_LABELS[self.game.end_reason], "body", 361, TEXT),
            ("Press R for a new round", "small", 411, MUTED),
        )
        for value, style, y, color in lines:
            glyph = self.fonts[style].render(value, True, color)
            self.screen.blit(glyph, glyph.get_rect(center=(288, y)))
