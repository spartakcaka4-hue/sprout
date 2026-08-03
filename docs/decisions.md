# Design Decisions

Each entry records the current v0.1 decision, why it was made, alternatives
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

Decision: Sprout v0.1 has global scope and one local scope per function call.
Blocks do not create scopes. Functions cannot mutate globals, and nested
functions are not supported.

Reason: this gives predictable behavior without closures, block-scope rules,
or a `global` keyword.

Alternatives considered: block scope, nested function scopes, and a global
mutation keyword.

Why rejected: each adds rules that v0.1 does not need.

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

Decision: v0.1 has no semicolons, chained comparisons, truthy values, type
annotations, int/float split, list mutation, block comments, or `global`
keyword.

Reason: each omission keeps the first version smaller and more explainable.

Alternatives considered: adding each feature now.

Why rejected: none is required by the v0.1 examples, and each adds extra
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

Reason: it is simple, familiar, and enough for v0.1.

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
would add rules not needed in v0.1.

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

Decision: `<`, `>`, `<=`, and `>=` work with Numbers only in v0.1.

Reason: numeric ordering is needed by examples; Text ordering raises questions
about case, locale, and character ordering.

Alternatives considered: lexicographic Text ordering and Boolean ordering.

Why rejected: both add behavior that is easy to misread and not needed for
v0.1.

Consequences: `"a" < "b"` is a runtime error for now.

## List Index Type

Decision: list indexes must be non-negative whole Numbers.

Reason: Sprout exposes one Number type, so `2.0` should work like `2`, while
`2.5` should not be silently rounded.

Alternatives considered: separate integer type, rounding, floor conversion,
or accepting negative indexes.

Why rejected: each adds a rule or feature outside v0.1.

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
v0.1.

Reason: the specified value set is Number, Text, Boolean, List, and `nothing`.
First-class functions would be an unplanned fifth kind of value.

Alternatives considered: allowing functions to be stored, printed, returned,
passed, compared, or placed in lists.

Why rejected: each requires additional rules for display, equality, and scope.

Consequences: code such as `copy = add` or `print(print)` is a runtime error.

## No Text Indexing

Decision: indexing works on Lists only in v0.1.

Reason: List indexing is needed for examples; Text indexing raises questions
about characters, escapes, and future Unicode behavior.

Alternatives considered: allowing `"abc"[0]`.

Why rejected: it is useful but not necessary for v0.1.

Consequences: use `length(text)` for Text length; direct Text indexing errors.

