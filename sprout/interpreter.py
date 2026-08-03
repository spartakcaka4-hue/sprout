from __future__ import annotations

from dataclasses import dataclass

from .ast_nodes import (
    Assignment,
    Binary,
    Call,
    Expression,
    ExpressionStatement,
    ForStatement,
    FunctionDef,
    IfStatement,
    Index,
    ListLiteral,
    Literal,
    Program,
    RepeatStatement,
    ReturnStatement,
    Statement,
    Unary,
    Variable,
)
from .builtins import NOTHING, BuiltinFunction, format_value, make_builtins, type_name
from .errors import SproutRuntimeError
from .lexer import TokenType


@dataclass(frozen=True)
class UserFunction:
    name: str
    params: list[str]
    body: list[Statement]
    line: int
    column: int

    @property
    def signature(self) -> str:
        return f"func {self.name}({', '.join(self.params)})"


class ReturnSignal(Exception):
    def __init__(self, value: object) -> None:
        self.value = value


class Interpreter:
    def __init__(self) -> None:
        self.output_lines: list[str] = []
        self.globals: dict[str, object] = make_builtins(self.output_lines)
        self.locals: dict[str, object] | None = None

    def run(self, program: Program) -> str:
        for statement in program.statements:
            self._execute(statement)
        if not self.output_lines:
            return ""
        return "\n".join(self.output_lines) + "\n"

    def _execute(self, statement: Statement) -> None:
        if isinstance(statement, Assignment):
            value = self._evaluate(statement.value)
            self._reject_function_value(value, statement.value.line, statement.value.column)
            self._assign(statement.name, value)
            return
        if isinstance(statement, ExpressionStatement):
            self._evaluate(statement.expression)
            return
        if isinstance(statement, IfStatement):
            self._execute_if(statement)
            return
        if isinstance(statement, RepeatStatement):
            self._execute_repeat(statement)
            return
        if isinstance(statement, ForStatement):
            self._execute_for(statement)
            return
        if isinstance(statement, FunctionDef):
            self.globals[statement.name] = UserFunction(
                statement.name,
                statement.params,
                statement.body,
                statement.line,
                statement.column,
            )
            return
        if isinstance(statement, ReturnStatement):
            value = NOTHING if statement.value is None else self._evaluate(statement.value)
            self._reject_function_value(value, statement.line, statement.column)
            raise ReturnSignal(value)
        raise AssertionError(f"Unhandled statement: {statement!r}")

    def _execute_if(self, statement: IfStatement) -> None:
        for condition, body in statement.branches:
            value = self._evaluate(condition)
            self._require_boolean(value, condition.line, condition.column, "Conditions must be Boolean values.")
            if value:
                self._execute_block(body)
                return
        if statement.else_body is not None:
            self._execute_block(statement.else_body)

    def _execute_repeat(self, statement: RepeatStatement) -> None:
        count_value = self._evaluate(statement.count)
        count = self._require_count(count_value, statement.count.line, statement.count.column)
        for index in range(count):
            if statement.counter_name is not None:
                self._assign(statement.counter_name, float(index))
            self._execute_block(statement.body)

    def _execute_for(self, statement: ForStatement) -> None:
        iterable = self._evaluate(statement.iterable)
        if type(iterable) is not list:
            raise SproutRuntimeError(
                statement.iterable.line,
                statement.iterable.column,
                "`for ... in` needs a list to iterate over.",
                f"Found: {type_name(iterable)}.",
            )
        for item in iterable:
            self._assign(statement.item_name, item)
            self._execute_block(statement.body)

    def _execute_block(self, statements: list[Statement]) -> None:
        for statement in statements:
            self._execute(statement)

    def _evaluate(self, expression: Expression) -> object:
        if isinstance(expression, Literal):
            if expression.literal_type == "nothing":
                return NOTHING
            return expression.value
        if isinstance(expression, Variable):
            return self._lookup(expression.name, expression.line, expression.column)
        if isinstance(expression, ListLiteral):
            values: list[object] = []
            for element in expression.elements:
                value = self._evaluate(element)
                self._reject_function_value(value, element.line, element.column)
                values.append(value)
            return values
        if isinstance(expression, Unary):
            return self._evaluate_unary(expression)
        if isinstance(expression, Binary):
            return self._evaluate_binary(expression)
        if isinstance(expression, Call):
            return self._evaluate_call(expression)
        if isinstance(expression, Index):
            return self._evaluate_index(expression)
        raise AssertionError(f"Unhandled expression: {expression!r}")

    def _evaluate_unary(self, expression: Unary) -> object:
        value = self._evaluate(expression.operand)
        if expression.operator_type == TokenType.MINUS:
            if type(value) is not float:
                raise SproutRuntimeError(
                    expression.line,
                    expression.column,
                    "Unary `-` only works with numbers.",
                    f"Found: {type_name(value)}.",
                )
            return -value
        if expression.operator_type == TokenType.NOT:
            self._require_boolean(
                value,
                expression.line,
                expression.column,
                "`not` needs a Boolean value.",
                f"Found: {type_name(value)}.",
            )
            return not value
        raise AssertionError(f"Unhandled unary operator: {expression.operator_type}")

    def _evaluate_binary(self, expression: Binary) -> object:
        if expression.operator_type == TokenType.AND:
            left = self._evaluate(expression.left)
            self._require_boolean(
                left,
                expression.line,
                expression.column,
                "`and` needs Boolean values on both sides.",
                f"Found: {type_name(left)} on the left.",
            )
            if not left:
                return False
            right = self._evaluate(expression.right)
            self._require_boolean(
                right,
                expression.line,
                expression.column,
                "`and` needs Boolean values on both sides.",
                f"Found: {type_name(right)} on the right.",
            )
            return bool(right)

        if expression.operator_type == TokenType.OR:
            left = self._evaluate(expression.left)
            self._require_boolean(
                left,
                expression.line,
                expression.column,
                "`or` needs Boolean values on both sides.",
                f"Found: {type_name(left)} on the left.",
            )
            if left:
                return True
            right = self._evaluate(expression.right)
            self._require_boolean(
                right,
                expression.line,
                expression.column,
                "`or` needs Boolean values on both sides.",
                f"Found: {type_name(right)} on the right.",
            )
            return bool(right)

        left = self._evaluate(expression.left)
        right = self._evaluate(expression.right)

        if expression.operator_type == TokenType.PLUS:
            return self._plus(left, right, expression)
        if expression.operator_type == TokenType.MINUS:
            return self._number_arithmetic(left, right, expression, lambda a, b: a - b)
        if expression.operator_type == TokenType.STAR:
            return self._number_arithmetic(left, right, expression, lambda a, b: a * b)
        if expression.operator_type == TokenType.SLASH:
            if type(left) is float and type(right) is float and right == 0:
                raise SproutRuntimeError(
                    expression.line,
                    expression.column,
                    "Division by zero.",
                    f"`{format_value(left)} / {format_value(right)}` has no defined result. Check that the divisor is never 0.",
                )
            return self._number_arithmetic(left, right, expression, lambda a, b: a / b)
        if expression.operator_type in (TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            if self._is_function_value(left) or self._is_function_value(right):
                raise SproutRuntimeError(
                    expression.line,
                    expression.column,
                    "Functions are not ordinary values in Sprout v0.1.",
                    "Call the function instead of comparing it.",
                )
            result = self._equals(left, right)
            return result if expression.operator_type == TokenType.EQUAL_EQUAL else not result
        if expression.operator_type in (
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
        ):
            return self._ordering(left, right, expression)
        raise AssertionError(f"Unhandled binary operator: {expression.operator_type}")

    def _evaluate_call(self, expression: Call) -> object:
        callee = self._evaluate(expression.callee)
        args: list[object] = []
        for arg in expression.args:
            value = self._evaluate(arg)
            self._reject_function_value(value, arg.line, arg.column)
            args.append(value)
        if isinstance(callee, BuiltinFunction):
            return callee.call(args, expression.line, expression.column)
        if isinstance(callee, UserFunction):
            if len(args) != len(callee.params):
                raise SproutRuntimeError(
                    expression.line,
                    expression.column,
                    f"`{callee.name}` expected {len(callee.params)} arguments but received {len(args)}.",
                    f"Check the call against the definition: {callee.signature}",
                )
            previous_locals = self.locals
            self.locals = {name: value for name, value in zip(callee.params, args)}
            try:
                try:
                    self._execute_block(callee.body)
                except ReturnSignal as signal:
                    return signal.value
                return NOTHING
            finally:
                self.locals = previous_locals
        raise SproutRuntimeError(
            expression.line,
            expression.column,
            f"Cannot call {type_name(callee)} as a function.",
            "Check that the name refers to a function.",
        )

    def _evaluate_index(self, expression: Index) -> object:
        collection = self._evaluate(expression.collection)
        if type(collection) is not list:
            raise SproutRuntimeError(
                expression.line,
                expression.column,
                "Indexing only works with lists in Sprout v0.1.",
                f"Found: {type_name(collection)}.",
            )
        index_value = self._evaluate(expression.index)
        index = self._require_index(index_value, expression.index.line, expression.index.column)
        if index >= len(collection):
            if len(collection) == 0:
                suggestion = "This list has no valid indexes."
            else:
                suggestion = f"Valid indexes for this list are 0 to {len(collection) - 1}."
            raise SproutRuntimeError(
                expression.line,
                expression.column,
                f"Index {index} is out of range for a list of length {len(collection)}.",
                suggestion,
            )
        return collection[index]

    def _plus(self, left: object, right: object, expression: Binary) -> object:
        if type(left) is float and type(right) is float:
            return left + right
        if type(left) is str and type(right) is str:
            return left + right
        if (type(left) is str and type(right) is float) or (type(left) is float and type(right) is str):
            raise SproutRuntimeError(
                expression.line,
                expression.column,
                "Cannot combine text and number with `+`.",
                f"Found: {type_name(left)} + {type_name(right)}.\nUse `print(\"Score:\", 10)` to print text and a number together.",
            )
        raise SproutRuntimeError(
            expression.line,
            expression.column,
            "`+` only works with two numbers or two text values.",
            f"Found: {type_name(left)} + {type_name(right)}.",
        )

    def _number_arithmetic(self, left: object, right: object, expression: Binary, operation) -> object:
        if type(left) is not float or type(right) is not float:
            raise SproutRuntimeError(
                expression.line,
                expression.column,
                f"`{expression.operator_lexeme}` only works with numbers.",
                f"Found: {type_name(left)} {expression.operator_lexeme} {type_name(right)}.",
            )
        return operation(left, right)

    def _ordering(self, left: object, right: object, expression: Binary) -> object:
        if type(left) is list or type(right) is list:
            raise SproutRuntimeError(
                expression.line,
                expression.column,
                "Lists can only be compared with `==` or `!=` in Sprout v0.1.",
            )
        if type(left) is not type(right):
            raise SproutRuntimeError(
                expression.line,
                expression.column,
                "Ordering comparisons need two values of the same supported type.",
                f"Found: {type_name(left)} {expression.operator_lexeme} {type_name(right)}.",
            )
        if type(left) is not float:
            raise SproutRuntimeError(
                expression.line,
                expression.column,
                "Ordering comparisons only work with numbers in Sprout v0.1.",
                f"Found: {type_name(left)}.",
            )
        if expression.operator_type == TokenType.LESS:
            return left < right
        if expression.operator_type == TokenType.LESS_EQUAL:
            return left <= right
        if expression.operator_type == TokenType.GREATER:
            return left > right
        if expression.operator_type == TokenType.GREATER_EQUAL:
            return left >= right
        raise AssertionError(f"Unhandled ordering operator: {expression.operator_type}")

    def _equals(self, left: object, right: object) -> bool:
        if type(left) is list and type(right) is list:
            if len(left) != len(right):
                return False
            return all(self._equals(a, b) for a, b in zip(left, right))
        if type(left) is not type(right):
            return False
        if left is NOTHING and right is NOTHING:
            return True
        return left == right

    def _require_boolean(
        self,
        value: object,
        line: int,
        column: int,
        message: str,
        suggestion: str | None = None,
    ) -> None:
        if type(value) is bool:
            return
        raise SproutRuntimeError(
            line,
            column,
            message,
            suggestion or "Use a comparison like `score != 0` to get a Boolean first.",
        )

    def _require_count(self, value: object, line: int, column: int) -> int:
        if type(value) is not float:
            raise SproutRuntimeError(
                line,
                column,
                "`repeat` needs a number of times to run.",
                f"Found: {type_name(value)}.",
            )
        if not value.is_integer():
            raise SproutRuntimeError(
                line,
                column,
                "`repeat` count must be a whole number.",
                "Use a number like 3, not 3.5.",
            )
        if value < 0:
            raise SproutRuntimeError(
                line,
                column,
                "`repeat` count cannot be negative.",
                "Use 0 if the loop should run zero times.",
            )
        return int(value)

    def _require_index(self, value: object, line: int, column: int) -> int:
        if type(value) is not float:
            raise SproutRuntimeError(
                line,
                column,
                "List indexes must be numbers.",
                f"Found: {type_name(value)}.",
            )
        if not value.is_integer():
            raise SproutRuntimeError(
                line,
                column,
                "List indexes must be whole numbers.",
                "Use an index like 0, 1, or 2.",
            )
        if value < 0:
            raise SproutRuntimeError(
                line,
                column,
                "Negative list indexes are not supported in Sprout v0.1.",
                "Use an index from 0 up to length(list) - 1.",
            )
        return int(value)

    def _lookup(self, name: str, line: int, column: int) -> object:
        if self.locals is not None and name in self.locals:
            return self.locals[name]
        if name in self.globals:
            return self.globals[name]
        raise SproutRuntimeError(
            line,
            column,
            f"`{name}` is not defined.",
            f"Check the spelling, or define it first with `{name} = ...`.",
        )

    def _assign(self, name: str, value: object) -> None:
        if self.locals is not None:
            self.locals[name] = value
        else:
            self.globals[name] = value

    def _is_function_value(self, value: object) -> bool:
        return isinstance(value, (BuiltinFunction, UserFunction))

    def _reject_function_value(self, value: object, line: int, column: int) -> None:
        if not self._is_function_value(value):
            return
        raise SproutRuntimeError(
            line,
            column,
            "Functions are not ordinary values in Sprout v0.1.",
            "Call the function by name instead of storing, printing, returning, or putting it in a list.",
        )
