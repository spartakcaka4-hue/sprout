from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Program:
    statements: list["Statement"]


class Statement:
    line: int
    column: int


class Expression:
    line: int
    column: int


@dataclass(frozen=True)
class Assignment(Statement):
    name: str
    value: Expression
    line: int
    column: int


@dataclass(frozen=True)
class ExpressionStatement(Statement):
    expression: Expression
    line: int
    column: int


@dataclass(frozen=True)
class IfStatement(Statement):
    branches: list[tuple[Expression, list[Statement]]]
    else_body: list[Statement] | None
    line: int
    column: int


@dataclass(frozen=True)
class RepeatStatement(Statement):
    count: Expression
    counter_name: str | None
    body: list[Statement]
    line: int
    column: int


@dataclass(frozen=True)
class ForStatement(Statement):
    item_name: str
    iterable: Expression
    body: list[Statement]
    line: int
    column: int


@dataclass(frozen=True)
class FunctionDef(Statement):
    name: str
    params: list[str]
    body: list[Statement]
    line: int
    column: int


@dataclass(frozen=True)
class ReturnStatement(Statement):
    value: Expression | None
    line: int
    column: int


@dataclass(frozen=True)
class Literal(Expression):
    value: Any
    literal_type: str
    line: int
    column: int


@dataclass(frozen=True)
class Variable(Expression):
    name: str
    line: int
    column: int


@dataclass(frozen=True)
class ListLiteral(Expression):
    elements: list[Expression]
    line: int
    column: int


@dataclass(frozen=True)
class Unary(Expression):
    operator_type: str
    operator_lexeme: str
    operand: Expression
    line: int
    column: int


@dataclass(frozen=True)
class Binary(Expression):
    left: Expression
    operator_type: str
    operator_lexeme: str
    right: Expression
    line: int
    column: int


@dataclass(frozen=True)
class Call(Expression):
    callee: Expression
    args: list[Expression]
    line: int
    column: int


@dataclass(frozen=True)
class Index(Expression):
    collection: Expression
    index: Expression
    line: int
    column: int

