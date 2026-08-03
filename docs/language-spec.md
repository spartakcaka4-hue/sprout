# Sprout v0.3 Language Specification

This document is the authoritative reference for Sprout v0.3.

Sprout is implemented as a lexer, parser, AST, and tree-walking interpreter.
It is not translated to Python source and executed with `exec()`.

## Files And Execution

Sprout source files use the provisional `.spr` extension.

Run a program with:

```text
sprout path/to/program.spr
```

Execution is top to bottom. A function definition creates the function only
when execution reaches that `func` statement.

From a source checkout, the compatibility launcher also supports:

```text
python sprout.py path/to/program.spr
```

## Lexical Rules

Comments start with `#` and run to the end of the line.

Blank lines and comment-only lines do not affect indentation.

Keywords are lowercase:

```text
if else repeat as for in func return true false nothing and or not exists
```

The built-in names `print` and `length` are reserved and cannot be
reused as variable, loop, parameter, or function names.

Names start with a letter or `_`, followed by letters, digits, or `_`.
Names are case-sensitive.

The v0.3 words `agent`, `uses`, `environment`, `type`, `world`, `size`,
`space`, `grid`, `continuous`, `place`, `tick`, `at`, and `when` are
contextual. They only have special meaning in the exact syntax forms
documented below. They may still be used as ordinary variable names when the
surrounding syntax is ordinary assignment or expression syntax.

## Indentation And Blocks

Blocks start with `:` and continue on the next line.

```text
if true:
    print("yes")
```

One indentation level is exactly 4 spaces. Tabs in indentation are syntax
errors. A block body must be exactly 4 spaces deeper than its header. All
statements in the same block must align. Dedents must return to an earlier
block level.

`if`, `else`, `else if`, `repeat`, `for`, `func`, `agent`, `environment`,
and `world` blocks must contain at least one statement or metadata item. There
is no `pass` statement.

## Values

Sprout v0.3 has four ordinary value types plus one no-value marker.

### Number

Numbers are Python `float` values.

Valid literals:

```text
0
5
123
0.5
5.0
123.456
```

Invalid literals:

```text
007
.5
5.
1_000
1e6
```

`/` always performs true division. `7 / 2` evaluates to `3.5`.
Floor division and modulus are not supported.

Numbers print using Python floating-point behavior, except whole values print
without `.0`.

```text
print(5.0)
print(0.1 + 0.2)
```

Output:

```text
5
0.30000000000000004
```

Division by zero is a runtime error.

### Text

Text uses double quotes only.

```text
name = "Ada"
```

Supported escapes are `\"`, `\\`, `\n`, and `\t`. Single quotes are not text
delimiters.

Text values print without surrounding quotes.

### Boolean

Booleans are lowercase:

```text
true
false
```

Conditions and logical operators require Boolean values. Sprout has no
truthiness.

### List

Lists are ordered, zero-indexed collections.

```text
foods = ["pizza", "apple", "bread"]
print(foods[0])
```

Lists may contain mixed value types and nested lists.

Indexing requires a non-negative whole Number. Negative indexes, non-whole
indexes, non-Number indexes, and out-of-range indexes are runtime errors.

List item assignment is not supported:

```text
foods[0] = "sushi"
```

List equality is structural and recursive. List ordering with `<`, `>`, `<=`,
or `>=` is always a runtime error.

### nothing

`nothing` represents no value.

Functions return `nothing` when they reach the end without `return` or use a
bare `return`.

```text
func done():
    return

print(done())
```

Output:

```text
nothing
```

`nothing == nothing` is `true`. Comparing `nothing` to any other type with
`==` is `false`.

## Variables And Scope

Use `=` to assign.

```text
score = 10
```

Use `==` to compare.

```text
print(score == 10)
```

Sprout has exactly two ordinary variable scope levels: global scope and one local scope for
each function call.

Blocks created by `if`, `repeat`, and `for` do not create new scopes. A
variable assigned inside one of those blocks stays visible in the surrounding
scope.

Inside a function:

- Reading a name checks local scope first, then global scope.
- Writing a name always creates or updates a local variable.
- A function can read a global but cannot mutate it.

Example:

```text
x = 10

func show():
    print(x)
    x = 5
    print(x)

show()
print(x)
```

Output:

```text
10
5
10
```

## Operators

Precedence from highest to lowest:

```text
() grouping, function calls, [] indexing
not, unary -
* /
+ -
== != < > <= >= exists
and
or
```

`+`, `-`, `*`, and `/` work on two Numbers.

`+` also concatenates two Text values.

Text plus Number is a runtime error. Use comma-separated `print` arguments
when printing different types together:

```text
print("Score:", score)
```

Arithmetic involving Boolean, List, `nothing`, or Text with `-`, `*`, or `/`
is a runtime error.

Ordering comparisons work with Numbers only. Ordering Lists is always
an error. Ordering Text, Boolean, or `nothing` is also out of scope.

Equality across different types never errors. It returns `false` for `==` and
`true` for `!=`.

```text
print(5 == "5")
print(0 == false)
```

Output:

```text
false
false
```

Chained comparisons are not supported:

```text
1 < x < 10
```

Use:

```text
1 < x and x < 10
```

## exists

Valid syntax:

```text
expression exists
```

`exists` is a postfix keyword operator. It is exact syntactic sugar for:

```text
expression != nothing
```

The parser turns `expression exists` into the same AST shape as
`expression != nothing`, so the interpreter uses the ordinary `!=` equality
rules. This means `exists` returns a Boolean for every normal value type, and
only `nothing` itself does not exist.

```text
print(0 exists)
print(false exists)
print("" exists)
print([] exists)
print(nothing exists)
```

Output:

```text
true
true
true
true
false
```

`exists` has the same precedence tier as `==` and `!=`, between arithmetic and
`and`/`or`.

```text
if winner exists and score > 0:
    print("Ready")
```

Scope behavior: `exists` adds no scope rules. The expression on the left is
evaluated normally before the comparison to `nothing`.

Important edge case: `exists` does not check whether a name was ever defined,
and it never catches lookup errors. A misspelled variable still raises the
ordinary undefined-variable runtime error:

```text
if winnner exists:
    print("won")
```

There is no special `exists` error type. Invalid usage is limited to the
normal expression grammar and the normal errors that can happen while
evaluating the left-hand expression, such as undefined-variable errors.

Example:

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

## Logical Operators

`and`, `or`, and `not` require Boolean operands.

`and` and `or` short-circuit:

```text
print(false and (10 / 0 > 2))
print(true or (10 / 0 > 2))
```

Output:

```text
false
true
```

The skipped side is not evaluated.

## if, else if, else

Syntax:

```text
if condition:
    statement
else if other_condition:
    statement
else:
    statement
```

Every condition must evaluate to Boolean. `if score:` is a runtime error when
`score` is a Number. Write an explicit comparison such as `if score != 0:`.

`else if` chains do not add extra indentation.

## repeat

Syntax:

```text
repeat count:
    statement

repeat count as name:
    statement
```

`count` must evaluate to a non-negative whole Number. A non-Number, non-whole
Number, or negative Number is a runtime error.

`repeat count as name` assigns `name` to `0`, `1`, `2`, up to `count - 1`.
The counter is an ordinary assignment in the current scope.

If the loop runs zero times, the counter assignment never happens. If the
counter did not exist before the loop, it remains undefined. If it did exist,
its previous value is unchanged.

## for in

Syntax:

```text
for item in list_value:
    statement
```

The value after `in` must be a List. Each element is assigned to the loop
variable in order. The loop variable is an ordinary assignment in the current
scope.

If the list is empty, the body runs zero times and the loop variable is not
assigned.

## Functions

Syntax:

```text
func add(a, b):
    return a + b
```

Function definitions are allowed only at the top level. Nested function
definitions are syntax errors.

Parameters are positional, required, and cannot be repeated. There are no
default values and no variadic parameters.

Calls use positional arguments:

```text
result = add(2, 3)
```

Calling with the wrong number of arguments is a runtime error.

Functions are not hoisted. Calling a function before execution reaches its
definition is an ordinary undefined-variable error.

Recursion is allowed:

```text
func fact(n):
    if n == 0:
        return 1
    else:
        return n * fact(n - 1)
```

`return` exits the function. A bare `return` or reaching the end returns
`nothing`. `return` outside a function is a parse-time syntax error.

Functions are not ordinary values. They cannot be stored, printed,
returned, compared, passed as arguments, or placed in lists.

## Built-In Functions

### print

```text
print(value1, value2, ...)
```

`print` accepts one or more arguments, converts each to display text, joins
them with a single space, and writes a newline.

### length

```text
length(value)
```

`length` accepts exactly one List or Text value and returns its length as a
Number.

## Tick Controls

Tick controls are top-level or block-level statements that manage the
interpreter's tick counter and automatic tick loop.

### tick.number

```text
tick.number
```

`tick.number` is a read-only expression. It starts at `0` for each
interpreter and increments only after one complete tick finishes. Failed or
partial ticks do not increment it.

In v0.3, a complete tick does not run world or agent behavior yet. It only
uses the shared internal tick execution path and then increments
`tick.number`.

### tick.start(rate)

```text
tick.start(30)
```

Starts automatic ticking at `rate` ticks per second. The rate must be a Number
greater than 0. Invalid rates are runtime errors.

Automatic ticking does not block the interpreter permanently. It runs until
paused, stopped, or a breakpoint triggers.

If an automatic tick session is already running or paused, `tick.start(rate)`
ends that session and starts a new one at the supplied rate.

### tick.pause

```text
tick.pause
```

Requests the current automatic tick session to pause. If a tick is currently
in progress, that tick is allowed to finish. The previous automatic rate is
remembered so `tick.resume` can continue with the same rate.

Calling `tick.pause` when no automatic session is running is a no-op.

### tick.resume

```text
tick.resume
```

Resumes a paused automatic tick session using the remembered rate. If there is
no paused automatic tick session, this is a runtime error.

### tick.next()

```text
tick.next()
tick.next(5)
```

Runs manual ticks. `tick.next()` runs exactly 1 complete tick.
`tick.next(n)` runs exactly `n` complete ticks. `n` must be a positive whole
Number.

Manual ticks use the same internal one-complete-tick execution path as
automatic ticks. In v0.3, breakpoints apply only to automatic ticking and do
not stop manual `tick.next(...)`.

### tick.stop

```text
tick.stop
```

Requests the current automatic tick session to stop. If a tick is currently in
progress, that tick is allowed to finish. Unlike `tick.pause`, stop forgets
the previous rate. After stop, the user must call `tick.start(rate)` again.

Calling `tick.stop` when no automatic session is running is allowed and leaves
the tick state idle.

### tick.break

```text
tick.break at 10
tick.break when tick.number >= 20
```

`tick.break at N` pauses automatic ticking after tick number `N` has
completed. `N` must be a positive whole Number.

`tick.break when condition` evaluates `condition` after each complete
automatic tick. The condition must evaluate to Boolean. If it evaluates to
true, automatic ticking pauses safely between ticks.

Breakpoints keep simulation state alive and inspectable. `tick.resume`
continues from a breakpoint pause using the previous rate.

## Agent Declarations

Agent declarations define agent metadata. They do not create live instances,
spawn anything, move anything, or run behavior in v0.3.

Syntax with presets:

```text
agent Blob uses:
    position.basic
    movement.ground
    biology.energy

    hunger = 5
    vision = 10
```

Syntax without presets:

```text
agent Note:
    label = "seed"
```

Agent declarations are top-level only. The agent name is stored in the
interpreter's agent metadata table, not in ordinary variable scope.
`print(Blob)` is still an undefined-variable error unless a normal variable
named `Blob` was assigned separately.

The `uses` section selects built-in presets. Preset selections have this exact
shape:

```text
category.preset
```

Only one preset may be selected from each category. Selecting two presets from
the same category is a runtime error.

Custom fields are ordinary field metadata with evaluated default values:

```text
hunger = 5
label = "seed"
```

Built-in fields and custom fields coexist. Duplicate field names are runtime
errors. For example, `biology.energy` injects `energy`, so declaring
`energy = 5` in the same agent is an error.

## Agent Preset Registry

Preset information is stored in the internal registry. Presets inject fields
and may carry metadata for future systems. They do not execute behavior.

### position

```text
position.none
```

No fields.

```text
position.basic
```

Fields: `x`, `y`.

```text
position.cell
```

Fields: `row`, `column`.

```text
position.continuous
```

Fields: `x`, `y`.

### movement

Movement presets store fields, allowed environment types, whether active
movement is possible, and a short description. They do not calculate movement.

```text
movement.none
```

Fields: none. Allowed environments: `ground`, `water`, `air`. Active
movement: false. Meaning: the agent cannot move by itself, but may be
associated with a supported environment as stationary metadata.

```text
movement.directional
```

Fields: `speed`, `direction`. Allowed environments: `ground`, `water`, `air`.
Active movement: true. This is a legacy generic movement metadata preset.

```text
movement.velocity
```

Fields: `velocity_x`, `velocity_y`. Allowed environments: `ground`, `water`,
`air`. Active movement: true. This is a legacy generic movement metadata
preset.

```text
movement.grid
```

Fields: `grid_x`, `grid_y`. Allowed environments: `ground`, `water`, `air`.
Active movement: true. This is a legacy generic movement metadata preset.

```text
movement.ground
```

Fields: `speed`, `direction`. Allowed environments: `ground`. Active
movement: true.

```text
movement.water
```

Fields: `speed`, `direction`. Allowed environments: `water`. Active
movement: true.

```text
movement.air
```

Fields: `speed`, `direction`, `altitude`. Allowed environments: `air`.
Active movement: true.

```text
movement.amphibious
```

Fields: `speed`, `direction`. Allowed environments: `ground`, `water`.
Active movement: true.

```text
movement.aerial_ground
```

Fields: `speed`, `direction`, `altitude`. Allowed environments: `ground`,
`air`. Active movement: true.

```text
movement.passive
```

Fields: `direction`. Allowed environments: `ground`, `water`, `air`. Active
movement: false. Meaning: the agent cannot initiate movement itself, but may
later be moved by external forces such as wind, currents, conveyors, or
another agent. Those forces are not implemented in v0.3.

### biology

```text
biology.none
```

No fields.

```text
biology.energy
```

Fields: `energy`, `alive`.

```text
biology.health
```

Fields: `health`, `max_health`, `alive`.

```text
biology.lifecycle
```

Fields: `age`, `lifespan`, `alive`.

## Environments

Environment declarations define named environment metadata. They do not create
worlds, render terrain, or run simulation.

Syntax:

```text
environment Land:
    type = ground
```

Supported environment types:

```text
ground
water
air
```

Invalid environment types are runtime errors. Duplicate environment names are
runtime errors.

Environment declarations are top-level only.

## Worlds

World declarations define bounded 2D space metadata and reference one default
environment. They do not render, generate terrain, contain regions, move
agents, or spawn instances in v0.3.

Syntax:

```text
world Meadow:
    size = 100, 80
    space = continuous
    environment = Land
```

Grid example:

```text
world Board:
    size = 20, 20
    space = grid
    environment = Ground
```

World declarations are top-level only.

Each world block must contain exactly these fields:

```text
size
space
environment
```

The fields may appear in any order. Extra fields are syntax errors. Missing or
duplicate fields are errors.

### size

Syntax:

```text
size = width, height
```

`width` and `height` are expressions. At runtime they must evaluate to
positive whole Numbers. Zero, negative values, non-whole values, and non-Number
values are runtime errors.

The valid x coordinate range is `0 <= x < width`. The valid y coordinate range
is `0 <= y < height`.

### space

Syntax:

```text
space = grid
space = continuous
```

`grid` and `continuous` are contextual metadata values here. They are not
ordinary variable lookups. Any other space type is a runtime error.

Grid worlds require whole-number placement coordinates. Continuous worlds allow
decimal placement coordinates.

### environment

Syntax:

```text
environment = Land
```

The name must refer to an environment that has already been declared. A world
has exactly one default environment in v0.3. Multiple regions, overlapping
environments, and multi-environment worlds are not supported yet.

World names are metadata only. A world declaration does not create an ordinary
variable named after the world.

## Placement Metadata

Placement declarations validate that an agent type can be associated with an
environment or world, then store metadata records for future spawning or
runtime work.

Environment placement syntax:

```text
place Blob in Land
```

Environment placement validation:

- The agent must already be declared.
- The environment must already be declared.
- The selected movement preset must allow the environment type.

Example:

```text
agent Blob uses:
    position.continuous
    movement.ground

environment Land:
    type = ground

place Blob in Land
```

Invalid example:

```text
agent Blob uses:
    position.continuous
    movement.ground

environment Sky:
    type = air

place Blob in Sky
```

This raises a runtime error similar to:

```text
Blob uses movement.ground and cannot be placed in an air environment.
```

If an agent has no movement preset, placement uses `movement.none`. In v0.3,
`movement.none` may be placed in any supported environment as stationary
metadata, and active movement is false.

`movement.passive` may also be placed in any supported environment, and active
movement remains false.

Duplicate placement declarations are allowed as separate metadata records.
They do not create live instances yet.

World placement syntax:

```text
place Blob in Meadow at 20, 35
```

World placement validation:

- The agent must already be declared.
- The world must already be declared.
- Coordinates must be Numbers.
- Grid-world coordinates must be whole Numbers.
- Continuous-world coordinates may be decimal Numbers.
- Coordinates must be inside the world's bounds.
- The selected movement preset must allow the world's default environment
  type.
- The selected position preset must be compatible with the world's space type.

Position compatibility:

```text
position.none        -> grid or continuous
position.basic       -> grid or continuous
position.cell        -> grid only
position.continuous  -> continuous only
```

An agent with no position preset behaves as `position.none` for world
placement.

World placement stores metadata including the world name, coordinates, space
type, default environment name and type, movement preset, allowed environments,
active movement flag, and position preset. It does not create a live agent
instance.

Duplicate world placement declarations are allowed as separate metadata
records.

## Unsupported In v0.3

The following are intentionally out of scope:

- Static type annotations
- Separate int and float types
- Exact decimal arithmetic
- Floor division and modulus
- Single-quoted text
- Scientific notation
- Underscore digit separators
- Truthiness
- Chained comparisons
- Nested function definitions
- Closures
- A `global` keyword
- List mutation, append, and item assignment
- Negative indexes
- Text indexing
- Block comments
- Empty blocks and `pass`
- A published PyPI release
- Live agent instances and spawning
- Agent behaviors
- Actual movement calculations
- Region maps and multi-environment worlds
- Tiles and terrain generation
- World rendering
- World transitions
- Pathfinding
- Steering behaviors such as seek, flee, or wander
- Collision physics
- Gravity
- Animation
- GUI rendering
- World generation
- Mutation
- Commands such as `move`, `walk`, `swim`, `fly`, `seek`, `flee`, or `wander`
