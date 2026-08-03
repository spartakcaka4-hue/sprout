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
class AgentPresetSelection:
    category: str
    preset: str
    line: int
    column: int


@dataclass(frozen=True)
class AgentFieldDeclaration:
    name: str
    value: Expression
    line: int
    column: int


@dataclass(frozen=True)
class AgentDeclaration(Statement):
    name: str
    uses_presets: bool
    presets: list[AgentPresetSelection]
    fields: list[AgentFieldDeclaration]
    line: int
    column: int


@dataclass(frozen=True)
class EnvironmentDeclaration(Statement):
    name: str
    environment_type: str
    line: int
    column: int


@dataclass(frozen=True)
class PlacementDeclaration(Statement):
    agent_name: str
    environment_name: str
    line: int
    column: int


@dataclass(frozen=True)
class WorldDeclaration(Statement):
    name: str
    width: Expression
    height: Expression
    space_type: str
    environment_name: str
    line: int
    column: int
    size_line: int
    size_column: int
    space_line: int
    space_column: int
    environment_line: int
    environment_column: int


@dataclass(frozen=True)
class WorldPlacementDeclaration(Statement):
    agent_name: str
    world_name: str
    x: Expression
    y: Expression
    line: int
    column: int


@dataclass(frozen=True)
class TickStatement(Statement):
    action: str
    argument: Expression | None
    line: int
    column: int


@dataclass(frozen=True)
class TickBreakStatement(Statement):
    kind: str
    condition: Expression
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
class TickNumber(Expression):
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
