# Sprout Syntax

Sprout programs are plain text files with the `.spr` extension.

Run one with:

```text
python sprout.py path/to/program.spr
```

## Values

Sprout v0.1 has Number, Text, Boolean, List, and `nothing`.

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
if score >= 10:
    print("You win")
else if score >= 5:
    print("Close")
else:
    print("Try again")
```

Write explicit comparisons, such as `if score != 0:`.

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
assignment are not supported in v0.1.

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
Functions are not ordinary values in v0.1: call them by name instead of
storing, printing, returning, or putting them in lists.

## Operators

From highest to lowest precedence:

```text
() calls and grouping, [] indexing
not, unary -
* /
+ -
== != < > <= >=
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

Ordering comparisons work with Numbers only in v0.1.

