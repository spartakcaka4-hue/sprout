# Errors

Every Sprout error uses this shape:

```text
Line <n>, column <n>:
<plain-language problem>
<optional suggestion>
```

Suggestions appear only when there is a clear likely fix.

Command-line usage errors, such as a missing file path or a missing file, are
reported by the `sprout` command without a Python traceback. Sprout syntax and
runtime errors preserve the formatted messages shown below.

## Syntax Errors

### Missing Indented Block

```text
Line 2, column 1:
Expected an indented block after `if`.
Indent the code that belongs in this block by 4 spaces.
```

Raised when a block header such as `if`, `else`, `repeat`, `for`, or `func`
is not followed by a 4-space-indented body.

### Tab In Indentation

```text
Line 2, column 1:
Found a tab character in the indentation.
Sprout uses spaces only. Replace tabs with 4 spaces per indentation level.
```

Raised when leading whitespace contains a tab.

### Bad Indentation

Raised when indentation is not a multiple of 4 spaces, a block body is not
exactly 4 spaces deeper than its header, or a dedent does not return to an
existing block level.

### Chained Comparison

```text
Line 1, column 9:
Chained comparisons like `1 < x < 10` are not supported yet.
Use `1 < x and x < 10` instead.
```

### Return Outside Function

```text
Line 1, column 1:
`return` can only be used inside a function.
```

### Nested Function Definition

Raised when `func` appears inside any block. Functions are top-level only.

### List Item Assignment

Raised for code such as:

```text
foods[0] = "sushi"
```

List item assignment is not supported.

### Built-In Name Reuse

Raised when user code tries to assign, define, or bind `print` or `length` as
a variable, loop name, parameter, or function name.

### Numeric Literal Errors

Raised for:

```text
007
.5
5.
1_000
1e6
```

Use ordinary decimal literals such as `7`, `0.5`, `5.0`, and `1000`.

### Malformed Tick Breakpoint

Raised for malformed breakpoint syntax such as:

```text
tick.break
tick.break on 3
```

Use:

```text
tick.break at 3
tick.break when tick.number >= 3
```

### Bad Agent Metadata Syntax

Raised when an `agent` block contains something other than preset names or
field assignments.

Preset names require an `agent Name uses:` header:

```text
agent Blob uses:
    position.basic
```

Custom-only agents may omit `uses`:

```text
agent Note:
    label = "seed"
```

### Bad Environment Syntax

Raised when an `environment` block does not set exactly one `type` field:

```text
environment Land:
    type = ground
```

### Bad World Syntax

Raised when a `world` block is malformed. A valid world block has exactly
`size`, `space`, and `environment` fields:

```text
world Meadow:
    size = 100, 80
    space = continuous
    environment = Land
```

Examples of syntax errors include missing fields, duplicate fields, unknown
fields, missing `=`, missing `,` between size values, and placing a world
declaration inside another block.

## Runtime Errors

### Undefined Variable

```text
Line 1, column 7:
`total` is not defined.
Check the spelling, or define it first with `total = ...`.
```

`exists` does not hide this error. `winnner exists` still raises the ordinary
undefined-variable error if `winnner` was never defined.

### Text Plus Number

```text
Line 1, column 17:
Cannot combine text and number with `+`.
Found: text + number.
Use `print("Score:", 10)` to print text and a number together.
```

### Arithmetic Type Error

Raised when arithmetic receives non-Number operands, except `+` between two
Text values, which concatenates.

### Division By Zero

```text
Line 1, column 10:
Division by zero.
`10 / 0` has no defined result. Check that the divisor is never 0.
```

### Non-Boolean Condition Or Logical Operand

Raised when `if`, `else if`, `and`, `or`, or `not` receives a non-Boolean
value. Sprout has no truthiness.

### Wrong Number Of Arguments

```text
Line 4, column 1:
`add` expected 2 arguments but received 1.
Check the call against the definition: func add(a, b)
```

### List Index Out Of Range

```text
Line 2, column 7:
Index 5 is out of range for a list of length 2.
Valid indexes for this list are 0 to 1.
```

### Bad List Index

Raised when a list index is not a Number, is not whole, or is negative.

### Bad Repeat Count

Raised when `repeat` receives a non-Number, a non-whole Number, or a negative
Number.

### Function Used As A Value

Functions are not ordinary values. It is an error to store, print, return,
compare, pass, or put a function in a list. Call functions by name.

### Invalid Tick Rate Or Count

Raised when:

```text
tick.start(0)
tick.start("fast")
tick.next(0)
tick.next(1.5)
```

`tick.start(rate)` needs a Number greater than 0. `tick.next(n)` needs a
positive whole Number.

### Resume Without A Paused Tick Session

Raised when `tick.resume` is used before an automatic tick session has been
paused.

### Invalid Tick Breakpoint

Raised when `tick.break at N` receives a non-positive or non-whole tick number,
or when `tick.break when condition` receives a condition that does not evaluate
to Boolean.

### Duplicate Agent Preset Category

Raised when an agent selects more than one preset from the same category:

```text
agent Blob uses:
    position.basic
    position.cell
```

### Duplicate Agent Field

Raised when a built-in preset field and a custom field, or two custom fields,
use the same name:

```text
agent Blob uses:
    biology.energy

    energy = 5
```

### Unknown Agent Preset Or Category

Raised when a preset category or preset name is not in the registry:

```text
agent Blob uses:
    behavior.basic
```

or:

```text
agent Blob uses:
    movement.fly
```

### Invalid Environment Type

Raised when an environment uses a type other than `ground`, `water`, or `air`:

```text
environment Desert:
    type = sand
```

### Duplicate World Name

Raised when two world declarations use the same name.

### Invalid World Size

Raised when `size = width, height` uses zero, negative, non-whole, or
non-Number values:

```text
world Meadow:
    size = 0, 10
    space = continuous
    environment = Land
```

World width and height must be positive whole Numbers.

### Invalid World Space Type

Raised when `space` is not `grid` or `continuous`:

```text
world Meadow:
    size = 100, 80
    space = hex
    environment = Land
```

### Unknown Environment In World

Raised when a world references an environment that has not already been
declared:

```text
world Meadow:
    size = 100, 80
    space = continuous
    environment = Land
```

### Duplicate Environment Name

Raised when two environment declarations use the same name.

### Unknown Agent Or Environment In Placement

Raised when `place Agent in Environment` references an agent or environment
that has not already been declared.

### Movement Environment Mismatch

Raised when an agent's movement preset does not allow the target environment
type:

```text
agent Blob uses:
    movement.ground

environment Sky:
    type = air

place Blob in Sky
```

The error explains which movement preset the agent uses and which environment
type rejected it.

### Unknown World In Placement

Raised when `place Agent in World at x, y` references a world that has not
already been declared.

### Invalid World Placement Coordinate

Raised when world placement coordinates are not Numbers, are decimal Numbers
in a grid world, or are outside bounds:

```text
place Blob in Meadow at 100, 35
```

For a world with width `100`, x must be at least `0` and less than `100`.

### Position World Mismatch

Raised when an agent's position preset is not compatible with the target
world's space type:

```text
agent Ant uses:
    position.cell
    movement.ground

environment Land:
    type = ground

world Meadow:
    size = 100, 80
    space = continuous
    environment = Land

place Ant in Meadow at 20, 35
```

`position.cell` is grid-only, and `position.continuous` is continuous-only.
