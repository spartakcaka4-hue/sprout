# Sprout v0.1 Language Specification

This document is the authoritative reference for Sprout v0.1.

Sprout is implemented as a lexer, parser, AST, and tree-walking interpreter.
It is not translated to Python source and executed with `exec()`.

## Files And Execution

Sprout source files use the provisional `.spr` extension.

Run a program with:

```text
python sprout.py path/to/program.spr
```

Execution is top to bottom. A function definition creates the function only
when execution reaches that `func` statement.

## Lexical Rules

Comments start with `#` and run to the end of the line.

Blank lines and comment-only lines do not affect indentation.

Keywords are lowercase:

```text
if else repeat as for in func return true false nothing and or not
```

The built-in names `print` and `length` are reserved in v0.1 and cannot be
reused as variable, loop, parameter, or function names.

Names start with a letter or `_`, followed by letters, digits, or `_`.
Names are case-sensitive.

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

`if`, `else`, `else if`, `repeat`, `for`, and `func` blocks must contain at
least one statement. There is no `pass` statement in v0.1.

## Values

Sprout v0.1 has four ordinary value types plus one no-value marker.

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
delimiters in v0.1.

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

Sprout v0.1 has exactly two scope levels: global scope and one local scope for
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
== != < > <= >=
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

Ordering comparisons work with Numbers only in v0.1. Ordering Lists is always
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
default values and no variadic parameters in v0.1.

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

Functions are not ordinary values in v0.1. They cannot be stored, printed,
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

## Unsupported In v0.1

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
- A packaged `sprout` shell command

