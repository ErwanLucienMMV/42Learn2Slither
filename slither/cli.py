"""Command-line options for the manual game."""

import argparse
import math
import sys


def speed_value(value: str) -> float:
    try:
        speed = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("speed must be a number") from None
    if not math.isfinite(speed) or not 1 <= speed <= 30:
        raise argparse.ArgumentTypeError("speed must be between 1 and 30")
    return speed


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Learn2Slither: a 10x10 Snake environment.",
        epilog="Start manual play with: python snake.py --play",
    )
    result.add_argument(
        "--play", action="store_true",
        help="open the game window with manual keyboard controls",
    )
    result.add_argument("--seed", type=int, help="reproducible initial board")
    result.add_argument(
        "--speed", type=speed_value, default=5.0,
        help="moves per second, 1 to 30 (default: 5)",
    )
    result.add_argument(
        "--step-by-step", action="store_true",
        help="move only on an arrow/WASD key or Enter",
    )
    result.add_argument(
        "--quiet", action="store_true",
        help="hide terminal vision and action output",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    command_line = parser()
    args = command_line.parse_args(argv)
    if not args.play:
        command_line.print_help()
        return 0
    try:
        import pygame
    except ModuleNotFoundError:
        print(
            "The display needs pygame-ce. "
            "Install it with: python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1
    from slither.display import GameWindow

    try:
        GameWindow(args.seed, args.speed, args.step_by_step, args.quiet).run()
    except pygame.error as error:
        print(f"Cannot open the game display: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        pygame.quit()
    return 0
