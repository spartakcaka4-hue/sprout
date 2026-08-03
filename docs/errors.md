# Errors

Every Sprout error uses this shape:

```text
Line <n>, column <n>:
<plain-language problem>
<optional suggestion>
```

Suggestions appear only when there is a clear likely fix.

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

Raised when `func` appears inside any block. Functions are top-level only in
v0.1.

### List Item Assignment

Raised for code such as:

```text
foods[0] = "sushi"
```

List item assignment is not supported in v0.1.

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

## Runtime Errors

### Undefined Variable

```text
Line 1, column 7:
`total` is not defined.
Check the spelling, or define it first with `total = ...`.
```

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

Functions are not ordinary values in v0.1. It is an error to store, print,
return, compare, pass, or put a function in a list. Call functions by name.

