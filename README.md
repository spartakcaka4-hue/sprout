# Sprout v0.3

Sprout is a small programming language designed to reduce boilerplate in
agent-based and simulation-focused projects.

It is implemented as a real lexer, parser, AST, and tree-walking interpreter
in Python. Sprout is experimental and not production-ready. The current v0.3
milestone focuses on clear syntax, metadata systems, and tick control rather
than live simulation.

## Overview

Sprout is exploring what a beginner-friendly, simulation-oriented language can
look like when common simulation concepts are part of the language surface.
Instead of immediately writing infrastructure for agents, environments, worlds,
and ticks, Sprout lets those concepts be declared directly.

Sprout currently stores metadata and validates compatibility. It does not yet
run agent behaviors, spawn live instances, render worlds, or execute movement.

## Example

```text
environment Land:
    type = ground

agent Blob uses:
    position.continuous
    movement.ground
    biology.energy

world Meadow:
    size = 100, 80
    space = continuous
    environment = Land

place Blob in Meadow at 20, 35

tick.next(3)
print(tick.number)
```

Output:

```text
3
```

This declares metadata for an environment, agent, world, and placement, then
advances the tick counter manually. It does not spawn or move a live Blob.

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

## Quick Start

Sprout currently runs from source. No package installer is provided yet.

Requirements:

- Python 3.11 or newer is recommended
- No third-party Python packages are required

Run an example from the repository root:

```text
python sprout.py examples/hello_world.spr
```

Run the v0.3 world metadata example:

```text
python sprout.py examples/world.spr
```

That example succeeds silently because metadata declarations do not print
anything unless the program calls `print`.

Run your own file:

```text
python sprout.py path/to/program.spr
```

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

Sprout v0.3 is an experimental milestone. The repository is suitable for
reading, testing, and language-design iteration, but the language is not stable
and should not be treated as production-ready.

The current implementation is intentionally conservative: metadata systems are
added before runtime simulation behavior so their syntax and validation rules
can be tested clearly.

## Current Limitations

Sprout does not currently implement:

- Live agent instances or spawning
- Agent behavior blocks
- Movement execution
- Pathfinding
- Seek, flee, wander, or steering behaviors
- Collision physics
- Gravity
- Rendering, animation, or GUI tools
- Terrain generation
- Multiple regions or overlapping environments inside a world
- World transitions
- Mutation
- Automatic agent updates during ticks
- A package installer or command-line shell beyond `python sprout.py file.spr`
- A VS Code extension

## Roadmap

Likely future areas:

- Live agent instances and spawning
- Runtime state inspection
- Movement execution built on the existing compatibility metadata
- Behavior syntax designed for simulation clarity
- World regions or richer environment maps
- Better editor support
- Packaging and installation

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

No license file is currently included.

TODO: choose and add a license before treating this as an open-source project
ready for public reuse.

## Documentation

- `docs/syntax.md` is the compact language guide.
- `docs/language-spec.md` is the detailed v0.3 reference.
- `docs/examples.md` explains example programs.
- `docs/errors.md` summarizes common error categories.
- `docs/decisions.md` records language-design decisions.
