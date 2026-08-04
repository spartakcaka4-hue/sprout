from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .errors import SproutRuntimeError


class NothingValue:
    def __repr__(self) -> str:
        return "nothing"


NOTHING = NothingValue()


@dataclass(frozen=True)
class BuiltinFunction:
    name: str
    signature: str
    callback: Callable[[list[object], int, int], object]

    def call(self, args: list[object], line: int, column: int) -> object:
        return self.callback(args, line, column)


def make_builtins(output_lines: list[str]) -> dict[str, BuiltinFunction]:
    def print_builtin(args: list[object], line: int, column: int) -> object:
        if len(args) == 0:
            raise SproutRuntimeError(
                line,
                column,
                "`print` needs at least 1 argument.",
                'Use `print("Hello")` or pass another value to print.',
            )
        output_lines.append(" ".join(format_value(arg) for arg in args))
        return NOTHING

    def length_builtin(args: list[object], line: int, column: int) -> object:
        if len(args) != 1:
            raise SproutRuntimeError(
                line,
                column,
                f"`length` expected 1 argument but received {len(args)}.",
                "Check the call against the definition: length(value)",
            )
        value = args[0]
        if type(value) is str or type(value) is list:
            return float(len(value))
        raise SproutRuntimeError(
            line,
            column,
            "`length` only works with text or lists.",
            f"Found: {type_name(value)}.",
        )

    return {
        "print": BuiltinFunction("print", "print(value1, value2, ...)", print_builtin),
        "length": BuiltinFunction("length", "length(value)", length_builtin),
    }


def type_name(value: object) -> str:
    if value is NOTHING:
        return "nothing"
    if type(value) is bool:
        return "boolean"
    if type(value) is float:
        return "number"
    if type(value) is str:
        return "text"
    if type(value) is list:
        return "list"
    if hasattr(value, "sprout_type_name"):
        return str(getattr(value, "sprout_type_name"))
    if isinstance(value, BuiltinFunction) or hasattr(value, "signature"):
        return "function"
    return type(value).__name__


def format_value(value: object) -> str:
    if value is NOTHING:
        return "nothing"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is float:
        if value.is_integer():
            return str(int(value))
        return str(value)
    if type(value) is str:
        return value
    if type(value) is list:
        return "[" + ", ".join(format_value(item) for item in value) + "]"
    if hasattr(value, "sprout_format_value"):
        return str(getattr(value, "sprout_format_value"))
    if isinstance(value, BuiltinFunction) or hasattr(value, "signature"):
        return "<function>"
    return str(value)
