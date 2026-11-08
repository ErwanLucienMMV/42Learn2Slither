# Usefull doc

Study notes for adding your own Q-learning agent. The repository currently
implements the environment and vision only; nothing here is executable training
code. Read [possible next steps.md](possible%20next%20steps.md) for the work order.

## Keep the subject's boundaries

The required model evaluates actions with a Q function. A Q-table or a neural
network approximating Q is allowed. A separate pathfinding controller or a
different learning algorithm would not satisfy that requirement.

The agent sees only `Vision`: four rays from the head. Never give it the full
grid, off-axis apple positions, the snake's complete body, global length,
statistics or a board-derived list of safe actions. The renderer can use those
for the human player. Learning can receive rewards and terminal flags without
making them extra decision inputs.

## Vocabulary

| Term | Meaning here |
| --- | --- |
| Observation `s` | The four rays, or your encoding of them |
| Action `a` | One of UP, LEFT, DOWN, RIGHT |
| Reward `r` | Your numeric feedback for a move |
| Episode / session | One random reset followed by moves until the round ends |
| Policy | The rule selecting an action from an observation |
| `Q(s, a)` | Estimated discounted future return after choosing `a` in `s` |
| Parameter | A learned table entry, network weight or bias |
| Hyperparameter | A setting you choose, such as learning rate or discount |
| Batch | A group of stored transitions used in one optimizer update |

## Understand tabular Q-learning first

A table associates an observation key with four action values. It updates the
entry for the action actually taken:

```text
target = reward                         if the next state is terminal
target = reward + gamma * max Q(next, a) otherwise
Q(state, action) += alpha * (target - Q(state, action))
```

`alpha` controls how quickly new information replaces old estimates. `gamma`
controls the importance of future rewards. An epsilon-greedy policy explores
with a random action some of the time and otherwise chooses a maximum-Q action.
Explore enough to discover useful moves before reducing epsilon.

For this board, the full ray tuple can be a table key, but many observations
will be rare. A smaller ray-derived representation generalizes by deliberately
discarding detail. Different hidden board layouts can also share the same
vision: the problem is partially observable, so a single observation need not
determine the entire future. Keep this limitation in mind when interpreting
results.

Read chapters 2 and 6 of Sutton and Barto's
[Reinforcement Learning: An Introduction](https://mitpress.mit.edu/9780262039246/reinforcement-learning/)
for exploration and temporal-difference methods.

## What the neural network does

A dense layer computes weighted sums plus biases. Nonlinear activations such as
ReLU let several layers represent more than one linear transformation. A small
multilayer perceptron is enough to start experimenting with ray observations.

One possible design to investigate is an input vector, two hidden layers, then
four outputs. The four outputs represent Q-values in a fixed action order; they
are scores for future return, not probabilities. Keep the last layer linear.
Use the subject order already defined by `Action`: UP, LEFT, DOWN, RIGHT.

Weights and biases are learned. Layer widths and the choice of activation are
settings you choose. Start small enough that you can inspect intermediate
values and train on a CPU.

The official [PyTorch model-building tutorial](https://docs.pytorch.org/tutorials/beginner/basics/buildmodel_tutorial.html)
explains `nn.Module`, dense layers and ReLU. Its final classification example
has a different objective from Q-value regression.

## Encode only what the snake sees

A concrete encoding to consider for this implementation:

1. Keep rays ordered UP, LEFT, DOWN, RIGHT, nearest cell first.
2. Reserve 10 slots per ray: the longest ray has nine board cells and its wall.
3. Keep the final `W`, then fill unused slots with a distinct PAD symbol.
4. Encode each slot as six categories: empty, body, green, red, wall, padding.

That gives 4 x 10 x 6 = 240 input numbers with one-hot encoding. This is a design
suggestion, not an implemented encoder. One-hot vectors avoid pretending that
numeric labels impose a meaningful order on cell types. You can compare a
smaller set of visible distances later, but do not silently discard information
without recording the change.

Do not append the game's global length or off-axis coordinates. The head is the
constant origin and does not need a feature. When the snake reaches zero length,
the terminal vision is empty; define a consistent terminal encoding and suppress
bootstrapping for that transition.

## Gradients and backpropagation

A loss measures the difference between a prediction and its target.
Backpropagation computes how that loss changes with each parameter. The
optimizer uses those gradients to adjust parameters. The learning rate controls
the update size; very large steps can destabilize learning, while very small
ones can make progress slow.

PyTorch tracks differentiable computations and provides gradients through
`loss.backward()`. Targets used as fixed reference values should not receive
gradients. Action selection during evaluation does not need a computation
graph.

Read [automatic differentiation](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
to understand graphs, parameter gradients and `no_grad`.

One optimizer iteration usually clears previous gradients, predicts the selected
action values, computes the loss, backpropagates, then updates parameters.
Gradients accumulate by default, so clearing them matters. Batch size controls
how many transitions contribute to that update. A loss decreasing on sampled
transitions is useful feedback but does not prove that the policy plays well.

Read [optimizing model parameters](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)
for the basic training mechanics before adapting them to a Q-learning target.

## From a table to DQN

Deep Q-learning approximates Q with a neural network. Store transitions
`(observation, action, reward, next_observation, terminated)` in a bounded replay
buffer. Sampling batches breaks up the strong correlation between consecutive
moves and reuses previous experience.

Keep an online network for learning and a target network for the next-state
estimate. Update the target network less directly, by periodic copying or a
slow blend. This helps keep the reference values from moving as quickly as the
predictions. Compute the target without tracking gradients:

```text
y = reward + gamma * (1 - terminated) * max Q_target(next_observation, a)
prediction = Q_online(observation, action_taken)
```

Only the selected action's prediction is compared with `y`. Huber loss is one
common option. Do not apply softmax to the Q outputs: their scale represents
return, rather than a probability distribution.

The official [DQN tutorial](https://docs.pytorch.org/tutorials/intermediate/reinforcement_q_learning.html)
explains replay, epsilon-greedy selection, target networks and the loss. Its
CartPole environment has different inputs and actions; adapt the concepts to
this subject's vision restriction.

For the research background, see Mnih and colleagues'
[Playing Atari with Deep Reinforcement Learning](https://arxiv.org/abs/1312.5602).
Its pixel-based architecture is not necessary for this small ray-based board.

## Rewards and episode endings

The environment returns facts through `StepResult.event`. Decide numeric rewards
in a separate interpreter. Start by distinguishing green, red, an ordinary move,
death and a full-board win. Death and win override the ordinary apple outcome;
for example, `ZERO_LENGTH` is a death caused by a red apple. The apple counters
still record what was eaten.

Choose scales that encourage growth without making endless safe loops more
valuable than reaching green apples. Change one reward rule at a time and keep
its definition beside the resulting checkpoint. Distance shaping must use only
permitted visible information if you introduce it; global apple coordinates
would bypass the observation restriction.

If you later add an external step limit, distinguish that cutoff (truncation)
from death or a win (termination). True terminal transitions have no next-state
bootstrap. An external time cutoff generally retains it. See Farama's
[explanation of termination and truncation](https://farama.org/Gymnasium-Terminated-Truncated-Step-API).
The current game has no step limit.

## Saving, resuming and evaluating

For inference, save network parameters together with architecture details,
encoding version and action order. Resuming training needs more: optimizer and
target-network state, exploration schedule, progress counters, configuration and
random-generator states. Preserve replay state too if you want a faithful
continuation. A table needs its entries and the same metadata relevant to it.

Use a single versioned checkpoint file as required by the subject. After loading,
verify identical Q predictions for a known observation. Frozen evaluation must
avoid optimizer steps and exploration-schedule changes. `model.eval()` changes
layer behavior; it does not, by itself, stop parameter updates. Pair evaluation
mode with gradient-free inference and an explicit no-learning control path.

The [PyTorch save/load guide](https://docs.pytorch.org/tutorials/beginner/basics/saveloadrun_tutorial.html)
covers parameter dictionaries and restoring a model. The
[checkpoint guide](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)
explains saving optimizer state as well.

Evaluate across multiple held-out seeds. Record final length, maximum length,
lifetime in moves, fraction ending at length 10 or more, and termination reasons.
Maximum length alone can hide a snake that later shrinks. Compare reward changes
on the same evaluation seeds, and keep training and evaluation results separate.

## When learning goes wrong

| Symptom | Investigate first |
| --- | --- |
| Immediate collisions never improve | Action indices, terminal targets, encoder order |
| Repeats a safe loop | Reward balance and exploration schedule |
| Loss explodes or becomes NaN | Learning rate, reward scale, gradients through targets |
| Training improves but evaluation does not | Random seeds, exploration, overfitting |
| Loaded model behaves differently | Encoder version, action order, missing parameters |
| Frozen evaluation changes the model | Optimizer calls, mutable table access, layer buffers |
| Good maximum length, poor final length | Red-apple handling and the evaluation metric |

Keep a short experiment log: configuration, seed, checkpoint, observation
encoding, reward definition and evaluation results. It will make both debugging
and the defense easier.
