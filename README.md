# Learn2Slither

A manual Snake game built around the Learn2Slither board rules. The environment,
four-direction vision and display are separate so an agent can be added later.
Rewards, Q-learning, neural networks, training and model files are left to
implement.

## Run

Python 3.10 or newer is required. From this directory on Windows:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe snake.py
```

On Linux or macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python snake.py
```

The game needs a graphical desktop. No external images, fonts, sound files or
GPU are required. The board starts paused so you can inspect it before moving.
`python -m slither` is an alternative entry point.

```sh
python snake.py --seed 17 --speed 3
python snake.py --step-by-step
python snake.py --quiet
python snake.py --help
```

`--speed` accepts 1 to 30 moves per second; the default is 5. `--seed` reproduces
the initial board and the sequence of random choices for the same actions.
New rounds continue that random sequence. To replay the exact first board,
relaunch with the same seed or call `reset(seed=...)` through the Python API.
`--quiet` suppresses the terminal vision and action log.

## Controls

| Input | Real time | Step mode |
| --- | --- | --- |
| Arrows / WASD | Select the next direction | Immediately move one cell |
| Space | Resume / pause | Move once in the selected direction |
| Enter | Move once and pause | Move once |
| Tab | Switch to step mode and pause | Switch to real time and pause |
| - / + | Decrease / increase speed | Set speed for real time |
| R | Start a new random round, paused | Same |
| Esc | Quit | Quit |

Buttons also provide resume, next move and restart. In real time, direction keys
while paused only change the next direction. If several are pressed before a
tick, the last direction is used. Reverse moves are accepted; if they enter the
body they end the round. The speed controls never make multiple moves in a
single render frame.

## Board rules

- Fixed 10x10 board, random contiguous three-cell snake, random direction.
- Two green apples and one red apple, always on distinct unoccupied cells when
  space permits. Green grows the snake by one; red shrinks it by one.
- A wall, any currently occupied body cell (including the tail), or a length of
  zero ends the round. A collision counts as an attempted move and leaves the
  last valid board visible.
- If space runs out, missing apples wait until a move frees cells. A missing red
  apple is restored first, then green apples up to two. The game continues with
  fewer apples until no green apple can remain, which shows the win screen.
  This happens at 99 snake cells with the red apple occupying the last cell;
  keeping the red apple makes a 100-cell snake unreachable through normal play.
- There is no starvation timer, wall wrapping, reversal filter or automatic
  restart.

The graphical display shows the complete board for the player. Before each
move, the terminal prints only the cross visible from the snake's head and the
chosen action. Its symbols are `W` wall, `H` head, `S` body, `G` green apple,
`R` red apple and `0` empty. Rays continue behind objects to the wall, matching
the subject's example.

## Python interface

```python
from slither import SnakeGame, observe

game = SnakeGame(seed=17)
print(observe(game).as_text())
result = game.turn_right()
print(result.event, result.terminated)
```

The four movement functions are `turn_up()`, `turn_left()`, `turn_down()` and
`turn_right()`. Each performs exactly one absolute move. `step("UP")` and
`step(Action.UP)` provide the same interface for a future controller. Movement
after termination raises `RuntimeError`; call `reset()` first. Invalid actions
raise `ValueError` before changing the board.

`StepResult` contains the action, event, termination flag, current length and
attempted move count. It deliberately has no numeric reward. `green_eaten`,
`red_eaten`, `max_length`, `steps` and `end_reason` support display and future
evaluation. `snake` is a head-first tuple of `(x, y)` cells; x grows right and y
grows down. Apple and snake properties return immutable snapshots.

`observe(game)` returns an immutable `Vision` with `up`, `left`, `down`, `right`
tuples. Each is nearest-first and includes its final wall. A zero-length snake
has four empty terminal rays. Give a future agent this observation only; the
board and statistics must not become extra policy inputs.

The core uses only the Python standard library and never imports Pygame. It can
be imported without opening a window or installing the display dependency.

## Files and remaining work

| File | Responsibility |
| --- | --- |
| `slither/environment.py` | Rules, reset, movement, apple placement, outcomes |
| `slither/vision.py` | Four-ray observation and terminal representation |
| `slither/display.py` | Window, manual controls, timing and rendering |
| `slither/cli.py` | Manual-game command-line options |
| [Usefull doc.md](Usefull%20doc.md) | Neural network and Q-learning study notes |
| [possible next steps.md](possible%20next%20steps.md) | Ordered implementation plan |

The game is the environment foundation, not the complete subject submission.
Session-count options, numeric rewards, agent decisions, checkpoint saving and
loading, frozen evaluation and trained models still need to be implemented.

## Style check

```sh
python -m pip install -r requirements-dev.txt
python -m flake8 snake.py slither
```

Use the virtual environment's Python as in the installation commands above.
There are no test files or test dependencies in the repository.
