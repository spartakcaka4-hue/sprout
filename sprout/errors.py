from __future__ import annotations


class SproutError(Exception):
    """Base class for user-facing Sprout errors."""

    def __init__(
        self,
        line: int,
        column: int,
        message: str,
        suggestion: str | None = None,
        *,
        found: str | None = None,
        expected: str | None = None,
    ) -> None:
        self.line = max(1, line)
        self.column = max(1, column)
        self.message = message
        self.suggestion = suggestion
        self.found = found
        self.expected = expected
        super().__init__(self.format())

    def format(self) -> str:
        lines = [
            f"Line {self.line}, column {self.column}:",
            self.message,
        ]
        if self.suggestion:
            lines.append(self.suggestion)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.format()


class SproutSyntaxError(SproutError):
    """A syntax error found before a program starts running."""


class SproutRuntimeError(SproutError):
    """A runtime error found while a program is running."""

