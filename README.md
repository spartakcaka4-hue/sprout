# Sprout v0.1

Sprout is a small beginner-friendly programming language implemented as a real
lexer, parser, AST, and tree-walking interpreter in Python.

The provisional file extension is `.spr`.

## Run a Program

From this directory:

```text
python sprout.py examples/hello_world.spr
```

You can run any `.spr` file the same way:

```text
python sprout.py path/to/program.spr
```

## Run the Tests

Sprout's tests use Python's built-in test runner, so no third-party test
package is required:

```text
python -m unittest discover -s tests
```

## Project Layout

```text
sprout/
    sprout/
        lexer.py
        parser.py
        ast_nodes.py
        interpreter.py
        errors.py
        builtins.py
    examples/
    docs/
    tests/
    sprout.py
```

Read `docs/syntax.md` for a compact language guide and
`docs/language-spec.md` for the full v0.1 behavior.

