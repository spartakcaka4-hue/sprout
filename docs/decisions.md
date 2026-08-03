# Design Decisions

Each entry records a current language decision, why it was made, alternatives
considered, why those alternatives were rejected for now, and consequences.

## Name And Extension

Decision: use the provisional name Sprout and the `.spr` file extension.

Reason: the name is short, friendly, and matches the beginner-friendly goal.

Alternatives considered: choosing a final public name now or using a generic
extension such as `.txt`.

Why rejected: public naming needs a trademark and ecosystem check; `.txt`
would hide that these files are source code.

Consequences: all code, docs, CLI examples, and tests use Sprout and `.spr`,
but this must be revisited before public release.

## `func`

Decision: use `func` to define functions.

Reason: it is quick to type and clearly signals a function definition.

Alternatives considered: `function` and `to`.

Why rejected: `function` is longer than needed; `to` reads too much like an
English preposition inside code.

Consequences: beginners learn one short keyword, and examples stay compact.

## Lowercase Booleans

Decision: use `true` and `false`.

Reason: every other keyword is lowercase, so booleans should be too.

Alternatives considered: `True` and `False`.

Why rejected: capitalized booleans would be an arbitrary exception.

Consequences: Sprout differs from Python here but becomes more consistent.

## `nothing`

Decision: use `nothing` as the no-value marker.

Reason: it reads plainly for beginners and prints as itself.

Alternatives considered: `null`, `nil`, and `None`.

Why rejected: those names are familiar in other languages but less plain in
ordinary English.

Consequences: functions without a value return `nothing`, and docs explain
that it is a value-like marker.

## No Truthiness

Decision: conditions and logical operators require Booleans.

Reason: implicit truthiness creates questions such as whether `0`, `""`, `[]`,
or `nothing` are true or false.

Alternatives considered: Python-style truthiness.

Why rejected: it is compact but hides several conversion rules.

Consequences: users write explicit comparisons such as `score != 0`; errors
are clearer at the cost of a little typing.

## `else if`

Decision: use the two-word form `else if`.

Reason: it reads directly as "otherwise, if".

Alternatives considered: `elif`.

Why rejected: `elif` is short but is an invented contraction beginners must
learn.

Consequences: chains stay flat without extra indentation, while code remains
readable.

## Two-Scope Model

Decision: Sprout has global scope and one local scope per function call.
Blocks do not create scopes. Functions cannot mutate globals, and nested
functions are not supported.

Reason: this gives predictable behavior without closures, block-scope rules,
or a `global` keyword.

Alternatives considered: block scope, nested function scopes, and a global
mutation keyword.

Why rejected: each adds rules that the current language does not need.

Consequences: a function can read globals but local assignment never leaks
out or mutates global state.

## Zero-Based Lists And Repeat Counters

Decision: list indexes and `repeat ... as` counters start at 0.

Reason: `repeat length(items) as i:` works naturally with `items[i]`.

Alternatives considered: one-based counters for beginner familiarity.

Why rejected: one-based counters would conflict with zero-based list indexes.

Consequences: "the fifth lap" uses counter value `4`; `syntax.md` shows the
worked example.

## Strict 4-Space Indentation

Decision: one indentation level is exactly 4 spaces, and tabs are rejected.

Reason: a single indentation rule is predictable and easy to explain.

Alternatives considered: Python-style flexible indentation and tab
normalization.

Why rejected: flexibility can make invisible whitespace mistakes harder to
spot; tab normalization hides what the file actually contains.

Consequences: some valid-looking code is rejected until aligned exactly.

## Deliberately Omitted Syntax

Decision: Sprout has no semicolons, chained comparisons, truthy values, type
annotations, int/float split, list mutation, block comments, or `global`
keyword.

Reason: each omission keeps the first version smaller and more explainable.

Alternatives considered: adding each feature now.

Why rejected: none is required by the current examples, and each adds extra
rules.

Consequences: users get clear errors or future-proposal notes instead of
partial behavior.

## `print` With Multiple Arguments

Decision: `print(value1, value2, ...)` is the way to print mixed types.

Reason: it avoids implicit Text/Number conversion while keeping beginner
printing convenient.

Alternatives considered: allowing `"Score: " + 10`.

Why rejected: automatic conversion hides type behavior and makes `+` do two
unrelated jobs across types.

Consequences: `+` stays strict; error messages suggest comma-separated
`print` when Text and Number are mixed.

## Float Numbers

Decision: implement Number as Python `float`.

Reason: it is simple, familiar, and enough for the current language.

Alternatives considered: `Decimal`.

Why rejected: decimal contexts and conversions would make the interpreter and
docs more complex.

Consequences: floating-point results such as `0.1 + 0.2` display as
`0.30000000000000004`; this is documented honestly.

## Numeric Literal Grammar

Decision: require an integer part, optional decimal part with digits on both
sides of `.`, no leading zeroes, no underscores, and no scientific notation.

Reason: the lexer should not invent rules for ambiguous number shapes.

Alternatives considered: `.5`, `5.`, `007`, `1_000`, and `1e6`.

Why rejected: each adds another special case or display expectation.

Consequences: users write `0.5`, `5.0`, `7`, `1000`, and full decimal forms.

## Boolean Logical Operators

Decision: `and`, `or`, and `not` require Boolean operands. `and` and `or`
short-circuit.

Reason: Boolean-only operands avoid truthiness, and short-circuiting is
predictable because the skipped side cannot affect the already-known result.

Alternatives considered: truthy logical operators or eager evaluation.

Why rejected: truthiness hides conversions; eager evaluation would make common
safe checks fail.

Consequences: `false and (10 / 0 > 2)` evaluates to `false` without division
by zero.

## List Equality And Ordering

Decision: list equality is structural and recursive. List ordering is always
a runtime error.

Reason: equality by contents is what beginners usually expect; ordering lists
has no single obvious beginner meaning.

Alternatives considered: Python object identity or lexicographic list
ordering.

Why rejected: identity would make equal-looking lists compare false; ordering
would add rules not needed in the current language.

Consequences: `[1, [2]] == [1, [2]]` is `true`, but `[1] < [2]` errors.

## Zero-Iteration Loop Variables

Decision: `repeat 0 as i` and `for x in []` do not assign their loop variable.

Reason: the binding is an ordinary assignment at the top of each iteration,
and zero iterations means no assignment occurs.

Alternatives considered: assigning `nothing` or `0` before the loop.

Why rejected: both would be invented hidden behavior.

Consequences: a pre-existing variable keeps its value; a new variable remains
undefined.

## Top-To-Bottom Function Definitions

Decision: `func` definitions take effect when execution reaches them.

Reason: this makes `func` behave like other top-level statements.

Alternatives considered: hoisting all functions before execution.

Why rejected: hoisting is a hidden pre-pass.

Consequences: calling a function before its definition is an ordinary
undefined-variable error.

## Parse-Time `return` Check

Decision: `return` outside a function is a syntax error.

Reason: the parser can detect it exactly and explain it before running the
program.

Alternatives considered: treating it as a runtime error.

Why rejected: runtime detection would delay a clear structural error.

Consequences: error snapshots pin the message for this case.

## Number-Only Ordering

Decision: `<`, `>`, `<=`, and `>=` work with Numbers only.

Reason: numeric ordering is needed by examples; Text ordering raises questions
about case, locale, and character ordering.

Alternatives considered: lexicographic Text ordering and Boolean ordering.

Why rejected: both add behavior that is easy to misread and not needed for
the current language.

Consequences: `"a" < "b"` is a runtime error for now.

## List Index Type

Decision: list indexes must be non-negative whole Numbers.

Reason: Sprout exposes one Number type, so `2.0` should work like `2`, while
`2.5` should not be silently rounded.

Alternatives considered: separate integer type, rounding, floor conversion,
or accepting negative indexes.

Why rejected: each adds a rule or feature outside the current language.

Consequences: `items[0]` and `items[2.0]` are valid; `items[2.5]` and
`items[-1]` error.

## Standalone Statements

Decision: only assignments and function calls can stand alone as statements.

Reason: evaluating `1 + 2` and discarding the result is unlikely to help
beginners.

Alternatives considered: allowing any expression statement.

Why rejected: it would silently do nothing visible in many cases.

Consequences: `greet()` is valid, but `1 + 2` is a syntax error.

## Duplicate Parameters

Decision: a function cannot list the same parameter name twice.

Reason: duplicate names make argument binding ambiguous to read.

Alternatives considered: allowing later parameters to overwrite earlier ones.

Why rejected: silent overwriting is hard to explain.

Consequences: `func bad(x, x):` is a syntax error.

## Built-In Names Are Reserved

Decision: `print` and `length` cannot be reused as variables, loop variables,
parameters, or function names.

Reason: overwriting basic tools would create confusing follow-on errors.

Alternatives considered: Python-style shadowing.

Why rejected: shadowing is flexible but surprising in a beginner language.

Consequences: users choose different names and built-ins remain reliable.

## Functions Are Not Values

Decision: functions can be called by name but are not ordinary values in
the current language.

Reason: the specified value set is Number, Text, Boolean, List, and `nothing`.
First-class functions would be an unplanned fifth kind of value.

Alternatives considered: allowing functions to be stored, printed, returned,
passed, compared, or placed in lists.

Why rejected: each requires additional rules for display, equality, and scope.

Consequences: code such as `copy = add` or `print(print)` is a runtime error.

## No Text Indexing

Decision: indexing works on Lists only.

Reason: List indexing is needed for examples; Text indexing raises questions
about characters, escapes, and future Unicode behavior.

Alternatives considered: allowing `"abc"[0]`.

Why rejected: it is useful but not necessary for the current language.

Consequences: use `length(text)` for Text length; direct Text indexing errors.

## `exists` As Sugar

Decision: add postfix `exists` as exact sugar for `!= nothing`.

Reason: `winner exists` reads naturally while keeping Sprout's Boolean and
equality rules unchanged.

Alternatives considered: a dedicated "is defined" check that would catch
undefined-variable lookup errors and return `false`.

Why rejected: swallowing lookup errors would hide typos, which conflicts with
Sprout's explicit-over-implicit principle.

Consequences: `exists` is technically redundant with `!= nothing` by design.
That redundancy is intentional: it improves readability without adding
truthiness or a new runtime concept.

## Tick Controls Before Simulation

Decision: v0.3 keeps tick controls independent from worlds, agent behavior,
and movement logic.

Reason: time control is a foundation for future simulation work, and it can be
tested independently.

Alternatives considered: adding ticks only after movement or world logic
exists.

Why rejected: coupling tick control to the first movement implementation would
make the timing API harder to validate in isolation.

Consequences: `tick.number`, manual ticking, automatic ticking, pause, resume,
stop, and breakpoints exist now. A complete v0.3 tick only advances the tick
counter.

## One Shared Tick Execution Path

Decision: manual ticks and automatic ticks call the same internal
one-complete-tick path.

Reason: future behavior should not drift depending on whether time advances
manually or automatically.

Alternatives considered: separate implementations for `tick.next(...)` and
the automatic loop.

Why rejected: separate paths would be easier to accidentally change
independently.

Consequences: adding future simulation work should happen in one place.

## Manual Ticks Ignore Breakpoints

Decision: v0.3 breakpoints pause automatic ticking but do not stop manual
`tick.next(...)`.

Reason: manual ticks are explicit user requests for an exact number of ticks.

Alternatives considered: applying breakpoints to both manual and automatic
ticks.

Why rejected: stopping manual ticks early would make `tick.next(10)` less
literal and harder to test.

Consequences: breakpoints are automatic-loop controls in v0.3.

## Agent Presets As Metadata

Decision: v0.3 agent presets inject fields and store metadata only. They do
not implement behavior.

Reason: presets remove boilerplate while keeping the first agent system small
and inspectable.

Alternatives considered: implementing movement, biology, or lifecycle behavior
inside presets immediately.

Why rejected: hidden behavior would make the first preset system too large and
harder to reason about.

Consequences: `agent Blob uses:` can declare useful structure, but no Blob
exists at runtime until a future spawning system is added.

## Preset Registry

Decision: built-in agent presets live in a registry-like data structure.

Reason: future categories and presets should be added by extending data, not
by growing parser or interpreter condition chains.

Alternatives considered: hardcoding each preset in parser or interpreter
branches.

Why rejected: that would mix syntax, validation, and preset content.

Consequences: categories such as `position`, `movement`, and `biology` are
easy to expand.

## One Preset Per Category

Decision: an agent may select only one preset from each category.

Reason: two presets from the same category can inject conflicting fields or
represent incompatible models.

Alternatives considered: allowing multiple presets and trying to merge them.

Why rejected: merge rules would require extra precedence and conflict rules.

Consequences: `position.basic` plus `position.cell` is a clear runtime error.

## Environments As Metadata

Decision: v0.3 has named environments with a simple `type` field, but no
world generation or rendering.

Reason: movement compatibility needs something to validate against before real
worlds exist.

Alternatives considered: waiting for a full world model before adding
environment declarations.

Why rejected: placement compatibility can be designed and tested as metadata
first.

Consequences: `environment Land: type = ground` stores metadata only.

## Placement Validates Compatibility But Does Not Spawn

Decision: `place Agent in Environment` validates declarations and movement
compatibility, then stores placement metadata without creating live instances.

Reason: placement compatibility is useful now, while spawning belongs to a
later runtime system.

Alternatives considered: making `place` create an agent instance immediately.

Why rejected: live instances require lifecycle, identity, storage, and future
mutation rules that v0.3 has not defined.

Consequences: duplicate placement declarations are allowed as separate
metadata records. They do not create duplicate live agents yet.

## `movement.none` Placement

Decision: `movement.none` may be placed in any supported environment as
stationary metadata, with active movement set to false.

Reason: stationary objects still need to be associated with environments.

Alternatives considered: rejecting all placements for `movement.none`.

Why rejected: that would make immobile agents impossible to place even as
metadata.

Consequences: compatibility validation distinguishes placement from active
movement.

## `movement.passive`

Decision: `movement.passive` may be placed in any supported environment, with
active movement set to false.

Reason: passive movement means the agent cannot initiate movement itself, not
that it cannot ever be moved by future external forces.

Alternatives considered: treating passive movement the same as no movement.

Why rejected: passive movement carries a different future meaning for wind,
currents, conveyors, or other agents.

Consequences: v0.3 stores the distinction in preset metadata but implements no
external forces.

## Worlds As Metadata

Decision: v0.3 worlds define bounded 2D metadata only.

Reason: placement and compatibility rules need a named space before real world
simulation, rendering, or terrain exists.

Alternatives considered: waiting for full world generation and rendering
before adding `world`.

Why rejected: world shape, bounds, and default environment can be designed and
tested independently.

Consequences: `world Meadow:` stores width, height, space type, and default
environment metadata, but no live scene is created.

## One Default Environment Per World

Decision: each v0.3 world has exactly one default environment.

Reason: this is enough to validate movement/environment compatibility while
keeping the first world system small.

Alternatives considered: supporting multiple regions, overlapping
environments, or region maps immediately.

Why rejected: those features require region syntax, lookup rules, and future
movement/runtime behavior.

Consequences: `environment = Land` is required, and multi-environment worlds
are deferred.

## Grid And Continuous Space

Decision: worlds choose either `grid` or `continuous` space.

Reason: these are the two basic coordinate models needed by current position
presets.

Alternatives considered: adding more space types such as hex, tile maps, or
unbounded space.

Why rejected: each would need more coordinate and compatibility rules.

Consequences: `space = grid` requires whole placement coordinates, while
`space = continuous` permits decimal coordinates.

## Bounded Coordinates

Decision: world placement coordinates must be inside `0 <= x < width` and
`0 <= y < height`.

Reason: bounded worlds need a clear half-open coordinate rule.

Alternatives considered: inclusive maximum bounds or automatic clamping.

Why rejected: inclusive maximum bounds would make `width` itself a valid x
coordinate, and clamping would hide errors.

Consequences: placing at `x = width` or `y = height` is a runtime error.

## Position Preset Compatibility

Decision: world placement validates position presets against world space.

Reason: `position.cell` and `position.continuous` represent different
coordinate models.

Alternatives considered: converting between cell and continuous coordinates
automatically.

Why rejected: conversion rules would be movement or spawning behavior, which
is outside v0.3.

Consequences: `position.cell` is grid-only, `position.continuous` is
continuous-only, `position.basic` works in both, and `position.none` works in
both as metadata.

## Separate World Placement Metadata

Decision: environment placements remain in `Interpreter.placements`, while
world placements are stored separately.

Reason: the two placement forms store different data. Environment placement
has no coordinates; world placement has coordinates, world space, and default
environment metadata.

Alternatives considered: one combined placement record with many optional
fields.

Why rejected: optional fields would make future runtime code harder to read.

Consequences: `place Blob in Land` and `place Blob in Meadow at 20, 35` are
preserved as distinct metadata paths.

## Installable Command Wrapper

Decision: package Sprout with the distribution name `sprout-lang`, while
keeping the import package named `sprout` and exposing the installed command
`sprout`.

Reason: users should be able to run `sprout program.spr` after installation
without changing the language interpreter or its syntax.

Alternatives considered: keeping only `python sprout.py program.spr`, or
rewriting the launcher around a new execution path.

Why rejected: source-only launching is awkward for users, and a rewrite would
risk changing tested interpreter behavior.

Consequences: the installed command and the legacy `python sprout.py` launcher
call the same `sprout.cli:main` function. Packaging is now ready for local
installation and distribution builds, but PyPI publication still requires a
human release step and license decision.
