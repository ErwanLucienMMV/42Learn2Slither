# possible next steps

The manual environment is ready. Work through these milestones in order; leave
the display usable while you build the learning side. The subject accepts a
Q-table or a neural network representing Q, so a table is a useful first
implementation before trying DQN.

## 1. Get comfortable with the board API

Run `python snake.py --seed 17 --step-by-step`. Compare the visible board with
the terminal cross. Try all four directions, both apple types, a reversal and a
wall collision. Read `slither/environment.py` and `slither/vision.py`.

The movement entry points are `turn_up`, `turn_left`, `turn_down`, `turn_right`,
or the shared `step(action)` method. All execute one move immediately. The
display's queued direction is a UI concern, not part of the environment API.

Done when you can explain which cells are visible, how growth and shrinkage work,
and why any occupied body cell is fatal. The crowded-board extension keeps
playing with fewer apples until no green apple can remain: 99 snake cells and
the red apple in the final cell. A 100-cell snake is unreachable while the red
apple stays on the board, because eating it would shrink the snake.

## 2. Define your agent-facing contract

Add an agent module whose decision method accepts only `Vision` or its encoding
and returns an `Action`. Keep `SnakeGame`, the full board and statistics outside
that decision method. Document a fixed output order: UP, LEFT, DOWN, RIGHT.

Add your encoder in the interpreter layer. You can start with immutable ray
tuples for table keys. For a network, consider the padded one-hot scheme in
[Usefull doc.md](Usefull%20doc.md), or design your own using only visible cells.
Record the schema so future checkpoints can detect incompatible encodings.

Done when the same vision always produces the same encoding, including a
zero-length terminal observation, and no hidden board data enters the policy.

## 3. Choose numeric rewards

Create a reward interpreter mapping move outcomes to numbers. Decide how to
handle ordinary movement, green apples, red apples, collisions, zero length and
a full-board win. Reward values are deliberately absent from the game code.

The environment preserves `green_eaten` and `red_eaten` counters even when a
terminal event takes precedence over an apple event. Keep this distinction clear
when deciding the terminal reward. Do not award the next episode's initial
state a reward for the previous episode's last action.

Done when you can write down the reward for every `Event` and explain how the
scales support growth and survival. Keep the definition with experiment results.

## 4. Implement tabular Q-learning

Build the Q-table, epsilon-greedy action selection and temporal-difference update
yourself. Start with the equations in the study notes. Every observation needs
four action values. Decide how to break equal-value ties so exploration is not
accidentally biased toward UP.

Inspect a few individual updates before running long sessions. Confirm that a
terminal transition uses only its immediate reward. A reverse action must still
be possible; do not use full-board knowledge to filter actions for the agent.

Done when a short, reproducible sequence changes only the intended table entries
and a no-learning run leaves the table unchanged.

## 5. Build the session runner

Add a controller outside the renderer. Its order is: observe, ask the agent,
apply one move, assign a reward, observe again, learn if enabled, then repeat.
Keep learning state across resets while resetting only the board each episode.
Use the terminal next observation for the final update before starting a new
round; never substitute the next round's initial observation.

Add command-line controls for the number of sessions, visual on/off and learning
on/off. The subject's example flags illustrate behavior; you can choose clear
spellings. The existing CLI handles only manual play. Reuse the current drawing
and step controls so an agent run can be inspected without introducing extra
moves between decisions.

For fast headless runs, skip window creation, render delays and terminal output.
The core already imports without Pygame. If you add an external episode step cap,
log it as truncation rather than turning it into a collision or zero-length
death. The study notes link the relevant bootstrap distinction.

Done when N requested sessions run, each terminal move is learned once, and
visual and headless runs take the same actions with the same random setup.

## 6. Save and restore one complete learning state

Add save/load options and a versioned checkpoint format. Include the Q-table
or network, its input schema, action order, hyperparameters, exploration state
and training counters. For a network, also preserve optimizer and target-network
state; include replay and random states if exact continuation is your goal.

Create `models/` when you have real checkpoints. Do not fill it with dummy files.
The subject expects one file describing each saved learning state. Write a
checkpoint safely so an interrupted save does not destroy the previous copy.

Done when loading restores identical predictions and the learning schedule
continues from the saved point. Document whether you resume at episode boundaries
or also support exact mid-episode restoration.

## 7. Add frozen evaluation and useful measurements

Make the no-learning option skip every update. For a network, use evaluation
mode and gradient-free inference too. Choose a fixed evaluation exploration
setting, normally greedy, and keep it distinct from the training schedule.

Record final length, maximum length, move count, end reason and how often final
length reaches 10. Keep a held-out set of seeds for comparisons. Use game
statistics for reports, never as extra decision inputs. An especially long
random run does not establish reliable performance.

Done when evaluation leaves saved parameters unchanged and produces comparable
reports over the same seeds.

## 8. Try a neural Q function if you want one

Read the linked PyTorch model, gradient and optimization tutorials before the
DQN tutorial. Implement the network, replay buffer, target network and minibatch
update yourself. Produce four unconstrained Q outputs; no classification
softmax is needed. Begin on a CPU with a small network.

Keep the same observation rules, action order, rewards and evaluation seeds
while replacing the table so you can make a useful comparison. Do not change
every hyperparameter at once. Add the chosen learning dependencies only when
you implement this stage; the manual game currently needs only pygame-ce.

Done when targets are detached, terminal states do not bootstrap, saved models
reload correctly, and measured play improves across more than one seed.

## 9. Produce the required models and prepare the defense

Save at least three real models trained for 1, 10 and 100 sessions respectively,
as required by the subject. Use clear filenames and record the configuration
and completed session count. Additional, longer training may be needed to
regularly finish with a snake of at least 10 cells and a long lifetime.

Demonstrate loading each model with learning disabled, at a readable visual
speed and in step mode. The graphical board should update once per action; the
terminal should show the restricted vision and action. Keep the display and
terminal logs optional during training.

Explain the Q update, reward choices, encoding, exploration schedule and model
format. Run `python -m flake8 snake.py slither` and include any new Python modules
in that check. Verify installation in a fresh virtual environment and ensure
the actual trained models are tracked in `models/`.

## 10. Consider bonuses after the mandatory behavior works

The subject suggests stronger final lengths, a richer interface, or changing
board size while reusing trained models. Leave the board at 10x10 for the
mandatory implementation. A larger board may require a compatible encoder or
retraining; do not assume a fixed 10-slot ray encoding transfers unchanged.
