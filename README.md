# Sprout v0.4.1

Sprout is a small programming language designed to reduce boilerplate in
agent-based and simulation-focused projects.

It is implemented as a real lexer, parser, AST, and tree-walking interpreter
in Python. Sprout is experimental and not production-ready. The current
v0.4.1 milestone is a runtime performance pass over v0.4 executable worlds.

## Overview

Sprout is exploring what a beginner-friendly, simulation-oriented language can
look like when common simulation concepts are part of the language surface.
Instead of writing all infrastructure for agents, environments, worlds, and
ticks by hand, Sprout lets those concepts be declared directly and then used
by a small deterministic runtime.

## Example

```text
environment Land:
    type = ground

agent Banana uses:
    position.cell
    movement.ground
    biology.energy

    every tick:
        energy = energy - 1
        move self by 1, 0

        if energy <= 0:
            remove self

world Kitchen:
    size = 10, 10
    space = grid
    environment = Land

spawn Banana as bob in Kitchen at 0, 4:
    energy = 3

tick.next(3)
print(bob exists)
```

Output:

```text
false
```

This spawns a live Banana, runs three sequential ticks, moves it one cell per
tick, and removes it when its energy reaches 0.

## Why Sprout Exists

Sprout is aimed at simulation-heavy projects where the same setup code appears
again and again: agents need fields, movement capabilities need constraints,
worlds need bounds, and simulation time needs a clear clock.

The project goal is not to replace Python or become a general-purpose Python
clone. Sprout is meant to explore a smaller language surface where simulation
ideas can be explicit, readable, and low-boilerplate.

## Current Features

- Number, Text, Boolean, List, and `nothing` values
- Variables, arithmetic, comparisons, Boolean logic, and `exists`
- `if`, `else if`, and `else`
- `repeat` loops and `for ... in` loops
- Functions and recursion
- Built-ins: `print` and `length`
- Tick controls: `tick.start`, `tick.pause`, `tick.resume`, `tick.next`,
  `tick.stop`, `tick.break`, and `tick.number`
- Agent metadata declarations with modular presets
- Position, movement, and biology preset registries
- Environment metadata with `ground`, `water`, and `air` types
- Environment placement validation with `place Agent in Environment`
- World metadata with bounded `grid` or `continuous` 2D space
- World placement validation with `place Agent in World at x, y`
- Live agent instances with `spawn Agent [as name] in World at x, y`
- Spawn-time field overrides with validation
- `every tick:` behavior blocks
- Sequential spawn-order tick updates
- Runtime movement with `move ... by` and `move ... to`
- Runtime removal with `remove`
- Dotted instance field reads such as `bob.energy`

## Quick Start

Requirements:

- Python 3.11 or newer is recommended
- No third-party Python packages are required

Install from a local checkout:

```text
python -m pip install .
```

Run a program:

```text
sprout path/to/program.spr
```

Run an example from the repository root after installation:

```text
sprout examples/hello_world.spr
```

Run directly from source without installing:

```text
python sprout.py examples/hello_world.spr
```

Run the world metadata example:

```text
sprout examples/world.spr
```

That example succeeds silently because metadata declarations do not print
anything unless the program calls `print`.

## Development Installation

Install in editable mode while working on Sprout:

```text
python -m pip install -e .
```

This installs the `sprout` command while keeping the package connected to the
source checkout.

## Examples

Example programs live in `examples/`.

```text
examples/hello_world.spr
examples/scores.spr
examples/loops.spr
examples/lists.spr
examples/functions.spr
examples/classify.spr
examples/exists.spr
examples/world.spr
```

The companion guide in `docs/examples.md` shows expected output where useful.

## VS Code Support

No VS Code extension is currently included in this repository.

If an extension is added later, this section should document how to install it,
which language features it supports, and whether it is bundled or developed as
a separate package.

## Running Tests

Sprout uses Python's built-in test runner:

```text
python -m unittest discover -s tests
```

The tests cover lexer, parser, interpreter behavior, examples, error
snapshots, ticks, agents, environments, worlds, and placement validation.

## Project Status

Sprout v0.4.1 is an experimental milestone. The repository is suitable for
reading, testing, and language-design iteration, but the language is not stable
and should not be treated as production-ready.

The current implementation is intentionally conservative: runtime simulation
exists, but it is still focused on deterministic movement, removal, and field
updates rather than full ecology, perception, or rendering systems.

## Current Limitations

Sprout does not currently implement:

- Pathfinding
- Seek, flee, wander, or steering behaviors
- Collision physics beyond one active grid agent per cell
- Gravity
- Rendering, animation, or GUI tools
- Terrain generation
- Multiple regions or overlapping environments inside a world
- World transitions
- Mutation or reproduction
- Food systems, combat, or perception queries
- A published PyPI release
- A VS Code extension

## Roadmap

Likely future areas:

- Runtime state inspection
- Speed budget enforcement
- World queries beyond width/height
- World regions or richer environment maps
- Better editor support
- PyPI publication

The roadmap is intentionally tentative. Features should earn their place by
making simulation code clearer or reducing repeated infrastructure.

## Contributing

Contributions and proposals should fit Sprout's simulation-focused direction.
Good changes should:

- reduce simulation boilerplate
- improve clarity for readers
- preserve the small-language feel
- fit the existing syntax and validation style
- avoid turning Sprout into a general-purpose Python clone

Small, focused changes are preferred. Include tests for language behavior and
update docs when syntax or user-visible behavior changes.

## License

Sprout is distributed under the license in `LICENSE`.

## Documentation

- `docs/syntax.md` is the compact language guide.
- `docs/language-spec.md` is the detailed v0.4 reference.
- `docs/performance-v0.4.1.md` records the v0.4.1 runtime benchmark work.
- `docs/examples.md` explains example programs.
- `docs/errors.md` summarizes common error categories.
- `docs/decisions.md` records language-design decisions.
