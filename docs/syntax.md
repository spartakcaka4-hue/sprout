# Sprout v0.3 Syntax

Sprout programs are plain text files with the `.spr` extension.

Run one with:

```text
python sprout.py path/to/program.spr
```

## Values

Sprout has Number, Text, Boolean, List, and `nothing`.

```text
score = 10
name = "Joel"
done = true
foods = ["pizza", "apple"]
missing = nothing
```

Numbers use Python-style floating-point behavior. That means this is expected:

```text
print(0.1 + 0.2)
```

Output:

```text
0.30000000000000004
```

Whole-number results print without `.0`, so `5.0` prints as `5`.

Text uses double quotes only. Supported escapes are `\"`, `\\`, `\n`, and
`\t`.

## Variables

Use `=` to assign and `==` to compare.

```text
score = 10
print(score == 10)
```

Names start with a letter or `_`, then may contain letters, digits, or `_`.
Keywords and built-in function names (`print`, `length`) cannot be reused as
variable, loop, parameter, or function names.

## Printing

Use commas to print several values with spaces between them:

```text
score = 10
print("Score:", score)
```

Output:

```text
Score: 10
```

Sprout does not combine Text and Numbers with `+`.

## Conditions

Conditions must be Boolean. Sprout has no truthiness.

```text
score = 10

if score >= 10:
    print("You win")
else if score >= 5:
    print("Close")
else:
    print("Try again")
```

Write explicit comparisons, such as `if score != 0:`.

Use `exists` to check whether a value is not `nothing`:

```text
winner = nothing

if winner exists:
    print("Winner:", winner)
else:
    print("No winner yet")
```

Output:

```text
No winner yet
```

`exists` means the same thing as `!= nothing`. It still evaluates the name on
the left normally, so a misspelled or undefined variable is still an error.

## Indentation

Blocks start with `:` and the body is indented exactly 4 spaces.

```text
if true:
    print("four spaces")
```

Tabs are always rejected in indentation. Empty blocks are not supported.

## Loops

Repeat a block a fixed number of times:

```text
repeat 3:
    print("Hello")
```

Use `as` to get a zero-based counter:

```text
repeat 3 as i:
    print("Lap", i)
```

Output:

```text
Lap 0
Lap 1
Lap 2
```

The counter is an ordinary variable assignment on each iteration. If the loop
runs zero times, the counter is not assigned.

Loop over list items:

```text
foods = ["pizza", "apple"]

for food in foods:
    print(food)
```

An empty list does not assign the loop variable unless it already had a value.

## Lists

Lists use square brackets and zero-based indexes.

```text
foods = ["pizza", "apple", "bread"]
print(foods[0])
print(length(foods))
```

Output:

```text
pizza
3
```

Indexes must be non-negative whole Numbers. Negative indexes and list item
assignment are not supported yet.

Lists compare structurally with `==` and `!=`:

```text
print([1, [2, 3]] == [1, [2, 3]])
```

Output:

```text
true
```

Ordering lists with `<`, `>`, `<=`, or `>=` is an error.

## Functions

Define functions with `func`.

```text
func add(a, b):
    return a + b

print(add(2, 3))
```

Output:

```text
5
```

Functions must be defined before they are called. There is no hoisting.
Functions can read globals, but assignments inside a function create or update
locals only.

A bare `return`, or reaching the end without `return`, gives `nothing`.
Functions are not ordinary values: call them by name instead of storing,
printing, returning, or putting them in lists.

## Tick Controls

Sprout v0.3 includes a tick-control system. A tick is one complete simulation
step. In v0.3, ticks only advance `tick.number`; no world or movement behavior
runs yet.

Run one manual tick:

```text
tick.next()
print(tick.number)
```

Output:

```text
1
```

Run several manual ticks:

```text
tick.next(5)
print(tick.number)
```

Output:

```text
5
```

Start automatic ticking:

```text
tick.start(30)
```

The rate is ticks per second and must be greater than 0. Automatic ticking
continues until paused, stopped, or a breakpoint triggers.

Pause and resume:

```text
tick.start(30)
tick.pause
tick.resume
tick.stop
```

`tick.pause` lets the current tick finish, then pauses. `tick.resume` continues
using the previous automatic tick rate. Resuming without a paused automatic
session is a runtime error.

Stop automatic ticking:

```text
tick.stop
```

`tick.stop` lets the current tick finish, then ends the automatic session and
forgets the previous rate.

Breakpoints:

```text
tick.break at 10
tick.break when tick.number >= 20
```

`tick.break at N` pauses automatic ticking after tick `N` completes.
`tick.break when condition` checks a Boolean condition after each automatic
tick. Breakpoints do not stop manual `tick.next(...)` calls in v0.3.

## Agent Declarations

Sprout v0.3 includes metadata-only agent declarations. Agents do not spawn, move,
render, act, mutate, or simulate yet.

Use built-in presets to add common fields:

```text
agent Blob uses:
    position.basic
    movement.ground
    biology.energy

    hunger = 5
    vision = 10
```

Built-in preset fields and custom fields coexist. Duplicate field names are a
runtime error:

```text
agent Blob uses:
    biology.energy

    energy = 5
```

Only one preset from each category may be selected:

```text
agent Blob uses:
    position.basic
    position.cell
```

This is a runtime error because both presets are from `position`.

You can declare custom-only agents without `uses`:

```text
agent Note:
    label = "seed"
```

### Agent Presets

Position presets:

```text
position.none          # no fields
position.basic         # x, y
position.cell          # row, column
position.continuous    # x, y
```

Movement presets:

```text
movement.none          # no fields; active movement false
movement.directional   # speed, direction
movement.velocity      # velocity_x, velocity_y
movement.grid          # grid_x, grid_y
movement.ground        # speed, direction
movement.water         # speed, direction
movement.air           # speed, direction, altitude
movement.amphibious    # speed, direction
movement.aerial_ground # speed, direction, altitude
movement.passive       # direction; active movement false
```

Biology presets:

```text
biology.none           # no fields
biology.energy         # energy, alive
biology.health         # health, max_health, alive
biology.lifecycle      # age, lifespan, alive
```

The newer movement presets also store allowed environment metadata. They do not
perform movement calculations.

## Environments And Placement

Environment declarations are metadata-only in v0.3:

```text
environment Land:
    type = ground

environment Lake:
    type = water

environment Sky:
    type = air
```

Supported environment types are:

```text
ground
water
air
```

Place an agent type in an environment:

```text
agent Blob uses:
    position.continuous
    movement.ground

environment Land:
    type = ground

place Blob in Land
```

`place` validates that the agent exists, the environment exists, and the
agent's movement preset allows the environment type. It stores placement
metadata only; it does not create live agent instances.

Invalid placement example:

```text
agent Blob uses:
    position.continuous
    movement.ground

environment Sky:
    type = air

place Blob in Sky
```

This raises a runtime error because `movement.ground` cannot be placed in an
air environment.

`movement.passive` may be placed in any supported environment, but active
movement remains false. `movement.none` may also be placed in supported
environments as stationary metadata, with active movement false.

## Worlds

World declarations are metadata-only in v0.3. They define bounded 2D space and
one default environment. They do not render anything, generate terrain, spawn
agents, or run movement.

Continuous world:

```text
environment Land:
    type = ground

world Meadow:
    size = 100, 80
    space = continuous
    environment = Land
```

Grid world:

```text
environment Ground:
    type = ground

world Board:
    size = 20, 20
    space = grid
    environment = Ground
```

World declarations are top-level only. Each world block must contain exactly
these fields, in any order:

```text
size = width, height
space = grid
environment = Land
```

`size` values must evaluate to positive whole Numbers. `space` must be
`grid` or `continuous`. `environment` must name an environment that was already
declared.

A world name is metadata only. It does not create an ordinary variable:

```text
print(Meadow)
```

is still an undefined-variable error unless a normal variable named `Meadow`
was assigned separately.

## World Placement

Place an agent type in a world with coordinates:

```text
agent Blob uses:
    position.continuous
    movement.ground

environment Land:
    type = ground

world Meadow:
    size = 100, 80
    space = continuous
    environment = Land

place Blob in Meadow at 20, 35
```

This stores world-placement metadata only. It does not create a live agent
instance.

Coordinate rules:

- Coordinates must be Numbers.
- In `grid` worlds, coordinates must be whole Numbers.
- In `continuous` worlds, decimal Numbers are allowed.
- `x` must be at least 0 and less than world width.
- `y` must be at least 0 and less than world height.

Position compatibility:

```text
position.cell        # grid worlds only
position.basic       # grid or continuous worlds
position.continuous  # continuous worlds only
position.none        # grid or continuous metadata placement
```

An agent with no position preset behaves like `position.none` for world
placement. Sprout does not infer or convert coordinates automatically.

World placement also validates the agent movement preset against the world's
default environment type, using the same compatibility rules as
`place Agent in Environment`.

## Operators

From highest to lowest precedence:

```text
() calls and grouping, [] indexing
not, unary -
* /
+ -
== != < > <= >= exists
and
or
```

`and` and `or` short-circuit, but they still require Boolean values when an
operand is evaluated.

Chained comparisons are not supported:

```text
1 < x < 10
```

Write:

```text
1 < x and x < 10
```

Ordering comparisons work with Numbers only.

## Still Out Of Scope

Sprout v0.3 does not include rendering, tiles, terrain generation, multiple
regions, overlapping environments, world transitions, pathfinding, steering
behaviors, collision physics, animation, GUI rendering, gravity, actual
movement calculations, live agent instances, spawning, mutation, automatic
agent updates during ticks, or commands such as `move`, `walk`, `swim`, `fly`,
`seek`, `flee`, or `wander`.
