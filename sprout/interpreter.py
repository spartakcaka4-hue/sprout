from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from .ast_nodes import (
    AgentDeclaration,
    Assignment,
    Binary,
    Call,
    EnvironmentDeclaration,
    Expression,
    ExpressionStatement,
    ForStatement,
    FunctionDef,
    IfStatement,
    Index,
    ListLiteral,
    Literal,
    PlacementDeclaration,
    Program,
    RepeatStatement,
    ReturnStatement,
    Statement,
    TickBreakStatement,
    TickNumber,
    TickStatement,
    Unary,
    Variable,
    WorldDeclaration,
    WorldPlacementDeclaration,
)
from .agent_presets import (
    PRESET_GROUPS,
    SUPPORTED_ENVIRONMENT_TYPES,
    SUPPORTED_WORLD_SPACE_TYPES,
    AgentDefinition,
    AgentFieldDefinition,
    AgentPreset,
    EnvironmentDefinition,
    PlacementDefinition,
    WorldDefinition,
    WorldPlacementDefinition,
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


@dataclass(frozen=True)
class ActiveTickBreakpoint:
    kind: str
    condition: Expression | None
    target: int | None
    line: int
    column: int


class Interpreter:
    def __init__(self) -> None:
        self.output_lines: list[str] = []
        self.globals: dict[str, object] = make_builtins(self.output_lines)
        self.locals: dict[str, object] | None = None
        self.agents: dict[str, AgentDefinition] = {}
        self.environments: dict[str, EnvironmentDefinition] = {}
        self.worlds: dict[str, WorldDefinition] = {}
        self.placements: list[PlacementDefinition] = []
        self.world_placements: list[WorldPlacementDefinition] = []
        self._tick_number = 0
        self._tick_condition = threading.Condition(threading.RLock())
        self._tick_state = "idle"
        self._tick_rate: float | None = None
        self._tick_previous_rate: float | None = None
        self._tick_request: str | None = None
        self._tick_thread: threading.Thread | None = None
        self._tick_breakpoints: list[ActiveTickBreakpoint] = []
        self._tick_error: SproutRuntimeError | None = None

    @property
    def tick_number(self) -> int:
        with self._tick_condition:
            return self._tick_number

    def run(self, program: Program) -> str:
        for statement in program.statements:
            self._execute(statement)
        if not self.output_lines:
            return ""
        return "\n".join(self.output_lines) + "\n"

    def _execute(self, statement: Statement) -> None:
        if isinstance(statement, AgentDeclaration):
            self._execute_agent_declaration(statement)
            return
        if isinstance(statement, EnvironmentDeclaration):
            self._execute_environment_declaration(statement)
            return
        if isinstance(statement, WorldDeclaration):
            self._execute_world_declaration(statement)
            return
        if isinstance(statement, PlacementDeclaration):
            self._execute_placement_declaration(statement)
            return
        if isinstance(statement, WorldPlacementDeclaration):
            self._execute_world_placement_declaration(statement)
            return
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
        if isinstance(statement, TickStatement):
            self._execute_tick_statement(statement)
            return
        if isinstance(statement, TickBreakStatement):
            self._execute_tick_break(statement)
            return
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

    def _execute_agent_declaration(self, statement: AgentDeclaration) -> None:
        selected_presets: dict[str, AgentPreset] = {}
        fields: dict[str, AgentFieldDefinition] = {}

        for preset_selection in statement.presets:
            preset = self._resolve_agent_preset(
                preset_selection.category,
                preset_selection.preset,
                preset_selection.line,
                preset_selection.column,
            )
            if preset.category in selected_presets:
                previous = selected_presets[preset.category]
                raise SproutRuntimeError(
                    preset_selection.line,
                    preset_selection.column,
                    f"Agent `{statement.name}` selects more than one `{preset.category}` preset.",
                    f"Use only one preset from each category; `{previous.full_name}` was already selected.",
                )
            selected_presets[preset.category] = preset
            for field_name in preset.fields:
                self._add_agent_field(
                    statement.name,
                    fields,
                    AgentFieldDefinition(field_name, "preset", preset.full_name, None, False),
                    preset_selection.line,
                    preset_selection.column,
                )

        for field_declaration in statement.fields:
            value = self._evaluate(field_declaration.value)
            self._reject_function_value(value, field_declaration.value.line, field_declaration.value.column)
            self._add_agent_field(
                statement.name,
                fields,
                AgentFieldDefinition(field_declaration.name, "custom", None, value, True),
                field_declaration.line,
                field_declaration.column,
            )

        self.agents[statement.name] = AgentDefinition(
            statement.name,
            selected_presets,
            fields,
            statement.line,
            statement.column,
        )

    def _execute_environment_declaration(self, statement: EnvironmentDeclaration) -> None:
        if statement.name in self.environments:
            raise SproutRuntimeError(
                statement.line,
                statement.column,
                f"Environment `{statement.name}` is already defined.",
                "Use a different environment name.",
            )
        if statement.environment_type not in SUPPORTED_ENVIRONMENT_TYPES:
            known = ", ".join(SUPPORTED_ENVIRONMENT_TYPES)
            raise SproutRuntimeError(
                statement.line,
                statement.column,
                f"Unknown environment type `{statement.environment_type}`.",
                f"Supported environment types: {known}.",
            )
        self.environments[statement.name] = EnvironmentDefinition(
            statement.name,
            statement.environment_type,
            statement.line,
            statement.column,
        )

    def _execute_world_declaration(self, statement: WorldDeclaration) -> None:
        if statement.name in self.worlds:
            raise SproutRuntimeError(
                statement.line,
                statement.column,
                f"World `{statement.name}` is already defined.",
                "Use a different world name.",
            )

        width_value = self._evaluate(statement.width)
        self._reject_function_value(width_value, statement.width.line, statement.width.column)
        height_value = self._evaluate(statement.height)
        self._reject_function_value(height_value, statement.height.line, statement.height.column)
        width = self._require_world_dimension(width_value, statement.width.line, statement.width.column, "width")
        height = self._require_world_dimension(height_value, statement.height.line, statement.height.column, "height")

        if statement.space_type not in SUPPORTED_WORLD_SPACE_TYPES:
            known = ", ".join(SUPPORTED_WORLD_SPACE_TYPES)
            raise SproutRuntimeError(
                statement.space_line,
                statement.space_column,
                f"Unknown world space type `{statement.space_type}`.",
                f"Supported world space types: {known}.",
            )

        environment = self.environments.get(statement.environment_name)
        if environment is None:
            raise SproutRuntimeError(
                statement.environment_line,
                statement.environment_column,
                f"World `{statement.name}` references unknown environment `{statement.environment_name}`.",
                "Declare the environment before the world.",
            )

        self.worlds[statement.name] = WorldDefinition(
            statement.name,
            width,
            height,
            statement.space_type,
            environment.name,
            environment.environment_type,
            statement.line,
            statement.column,
        )

    def _execute_placement_declaration(self, statement: PlacementDeclaration) -> None:
        agent = self.agents.get(statement.agent_name)
        if agent is None:
            raise SproutRuntimeError(
                statement.line,
                statement.column,
                f"Cannot place unknown agent `{statement.agent_name}`.",
                "Declare the agent before placing it.",
            )

        environment = self.environments.get(statement.environment_name)
        if environment is None:
            raise SproutRuntimeError(
                statement.line,
                statement.column,
                f"Cannot place `{statement.agent_name}` in unknown environment `{statement.environment_name}`.",
                "Declare the environment before using `place`.",
            )

        movement_preset = self._movement_preset_for_agent(agent)
        self._validate_movement_environment_compatibility(
            agent,
            movement_preset,
            environment.environment_type,
            statement.line,
            statement.column,
        )

        self.placements.append(
            PlacementDefinition(
                agent.name,
                environment.name,
                environment.environment_type,
                movement_preset.full_name,
                movement_preset.can_move_actively,
                statement.line,
                statement.column,
            )
        )

    def _execute_world_placement_declaration(self, statement: WorldPlacementDeclaration) -> None:
        agent = self.agents.get(statement.agent_name)
        if agent is None:
            raise SproutRuntimeError(
                statement.line,
                statement.column,
                f"Cannot place unknown agent `{statement.agent_name}`.",
                "Declare the agent before placing it.",
            )

        world = self.worlds.get(statement.world_name)
        if world is None:
            raise SproutRuntimeError(
                statement.line,
                statement.column,
                f"Cannot place `{statement.agent_name}` in unknown world `{statement.world_name}`.",
                "Declare the world before using `place ... at`.",
            )

        movement_preset = self._movement_preset_for_agent(agent)
        self._validate_movement_environment_compatibility(
            agent,
            movement_preset,
            world.environment_type,
            statement.line,
            statement.column,
        )
        position_preset = self._position_preset_for_agent(agent)
        self._validate_position_world_compatibility(
            agent,
            position_preset,
            world,
            statement.line,
            statement.column,
        )

        x_value = self._evaluate(statement.x)
        self._reject_function_value(x_value, statement.x.line, statement.x.column)
        y_value = self._evaluate(statement.y)
        self._reject_function_value(y_value, statement.y.line, statement.y.column)
        x = self._require_world_coordinate(x_value, statement.x.line, statement.x.column, "x", world)
        y = self._require_world_coordinate(y_value, statement.y.line, statement.y.column, "y", world)

        self.world_placements.append(
            WorldPlacementDefinition(
                agent.name,
                world.name,
                x,
                y,
                world.space_type,
                world.environment_name,
                world.environment_type,
                movement_preset.full_name,
                movement_preset.allowed_environments,
                movement_preset.can_move_actively,
                position_preset.full_name,
                statement.line,
                statement.column,
            )
        )

    def _movement_preset_for_agent(self, agent: AgentDefinition) -> AgentPreset:
        preset = agent.selected_presets.get("movement")
        if preset is not None:
            return preset
        return PRESET_GROUPS["movement"]["none"]

    def _position_preset_for_agent(self, agent: AgentDefinition) -> AgentPreset:
        preset = agent.selected_presets.get("position")
        if preset is not None:
            return preset
        return PRESET_GROUPS["position"]["none"]

    def _validate_movement_environment_compatibility(
        self,
        agent: AgentDefinition,
        movement_preset: AgentPreset,
        environment_type: str,
        line: int,
        column: int,
    ) -> None:
        if environment_type in movement_preset.allowed_environments:
            return
        article = "an" if environment_type[0] in "aeiou" else "a"
        raise SproutRuntimeError(
            line,
            column,
            f"{agent.name} uses {movement_preset.full_name} and cannot be placed in {article} {environment_type} environment.",
            f"Allowed environments for {movement_preset.full_name}: {', '.join(movement_preset.allowed_environments) or 'none'}.",
        )

    def _validate_position_world_compatibility(
        self,
        agent: AgentDefinition,
        position_preset: AgentPreset,
        world: WorldDefinition,
        line: int,
        column: int,
    ) -> None:
        compatible_spaces = {
            "position.none": ("grid", "continuous"),
            "position.basic": ("grid", "continuous"),
            "position.cell": ("grid",),
            "position.continuous": ("continuous",),
        }
        allowed_spaces = compatible_spaces.get(position_preset.full_name, ())
        if world.space_type in allowed_spaces:
            return
        raise SproutRuntimeError(
            line,
            column,
            f"{agent.name} uses {position_preset.full_name} and cannot be placed in world `{world.name}` with {world.space_type} space.",
            "Choose a compatible position preset or world space type.",
        )

    def _resolve_agent_preset(self, category: str, preset_name: str, line: int, column: int) -> AgentPreset:
        category_presets = PRESET_GROUPS.get(category)
        if category_presets is None:
            known = ", ".join(PRESET_GROUPS)
            raise SproutRuntimeError(
                line,
                column,
                f"Unknown agent preset category `{category}`.",
                f"Known categories: {known}.",
            )

        preset = category_presets.get(preset_name)
        if preset is None:
            known = ", ".join(category_presets)
            raise SproutRuntimeError(
                line,
                column,
                f"Unknown `{category}` preset `{preset_name}`.",
                f"Known `{category}` presets: {known}.",
            )
        return preset

    def _add_agent_field(
        self,
        agent_name: str,
        fields: dict[str, AgentFieldDefinition],
        field: AgentFieldDefinition,
        line: int,
        column: int,
    ) -> None:
        existing = fields.get(field.name)
        if existing is not None:
            existing_source = (
                f"`{existing.preset}`"
                if existing.source == "preset" and existing.preset is not None
                else "a custom field"
            )
            raise SproutRuntimeError(
                line,
                column,
                f"Field `{field.name}` already exists on agent `{agent_name}`.",
                f"It was added by {existing_source}; choose a different field name.",
            )
        fields[field.name] = field

    def _execute_tick_statement(self, statement: TickStatement) -> None:
        if statement.action == "start":
            assert statement.argument is not None
            rate_value = self._evaluate(statement.argument)
            rate = self._require_tick_rate(rate_value, statement.argument.line, statement.argument.column)
            self._start_automatic_ticks(rate)
            return
        if statement.action == "pause":
            self._pause_automatic_ticks()
            return
        if statement.action == "resume":
            self._resume_automatic_ticks(statement.line, statement.column)
            return
        if statement.action == "next":
            if statement.argument is None:
                count = 1
            else:
                count_value = self._evaluate(statement.argument)
                count = self._require_tick_count(count_value, statement.argument.line, statement.argument.column)
            for _ in range(count):
                self._execute_one_complete_tick()
            return
        if statement.action == "stop":
            self._stop_automatic_ticks()
            return
        raise AssertionError(f"Unhandled tick action: {statement.action}")

    def _execute_tick_break(self, statement: TickBreakStatement) -> None:
        if statement.kind == "at":
            target_value = self._evaluate(statement.condition)
            target = self._require_tick_break_target(
                target_value,
                statement.condition.line,
                statement.condition.column,
            )
            breakpoint = ActiveTickBreakpoint("at", None, target, statement.line, statement.column)
        elif statement.kind == "when":
            self._require_tick_break_condition(statement.condition)
            breakpoint = ActiveTickBreakpoint("when", statement.condition, None, statement.line, statement.column)
        else:
            raise AssertionError(f"Unhandled tick breakpoint kind: {statement.kind}")

        with self._tick_condition:
            self._tick_breakpoints.append(breakpoint)

    def _start_automatic_ticks(self, rate: float) -> None:
        self._stop_automatic_ticks()
        self._begin_automatic_tick_thread(rate)

    def _pause_automatic_ticks(self) -> None:
        with self._tick_condition:
            if self._tick_state == "running":
                self._tick_request = "pause"
                self._tick_condition.notify_all()
                while self._tick_state == "running":
                    self._tick_condition.wait()
            error = self._tick_error
            self._tick_error = None
        if error is not None:
            raise error

    def _resume_automatic_ticks(self, line: int, column: int) -> None:
        with self._tick_condition:
            if self._tick_state != "paused" or self._tick_previous_rate is None:
                raise SproutRuntimeError(
                    line,
                    column,
                    "Cannot resume ticking because there is no paused automatic tick session.",
                    "Call `tick.start(rate)` first, or resume only after `tick.pause` or a tick breakpoint.",
                )
            rate = self._tick_previous_rate
            self._tick_error = None
        self._begin_automatic_tick_thread(rate)

    def _stop_automatic_ticks(self) -> None:
        with self._tick_condition:
            if self._tick_state == "running":
                self._tick_request = "stop"
                self._tick_condition.notify_all()
                while self._tick_state == "running":
                    self._tick_condition.wait()
            else:
                self._tick_state = "idle"
                self._tick_rate = None
                self._tick_previous_rate = None
                self._tick_request = None
                self._tick_thread = None
            error = self._tick_error
            self._tick_error = None
        if error is not None:
            raise error

    def _begin_automatic_tick_thread(self, rate: float) -> None:
        thread = threading.Thread(
            target=self._automatic_tick_loop,
            args=(rate,),
            name="SproutTickLoop",
            daemon=True,
        )
        with self._tick_condition:
            self._tick_state = "running"
            self._tick_rate = rate
            self._tick_previous_rate = rate
            self._tick_request = None
            self._tick_error = None
            self._tick_thread = thread
        thread.start()

    def _automatic_tick_loop(self, rate: float) -> None:
        interval = 1.0 / rate
        next_tick_at = time.monotonic() + interval

        while True:
            with self._tick_condition:
                while True:
                    if self._tick_request in ("pause", "stop"):
                        self._finish_automatic_ticks(self._tick_request)
                        return
                    remaining = next_tick_at - time.monotonic()
                    if remaining <= 0:
                        break
                    self._tick_condition.wait(remaining)

            try:
                self._execute_one_complete_tick()
                should_pause = self._tick_breakpoint_triggered()
            except SproutRuntimeError as error:
                with self._tick_condition:
                    self._tick_error = error
                    self._finish_automatic_ticks("pause")
                return

            with self._tick_condition:
                if self._tick_request in ("pause", "stop"):
                    self._finish_automatic_ticks(self._tick_request)
                    return
                if should_pause:
                    self._finish_automatic_ticks("pause")
                    return

            next_tick_at += interval
            now = time.monotonic()
            if next_tick_at < now:
                next_tick_at = now

    def _finish_automatic_ticks(self, request: str | None) -> None:
        if request == "stop":
            self._tick_state = "idle"
            self._tick_rate = None
            self._tick_previous_rate = None
        else:
            self._tick_state = "paused"
            self._tick_rate = None
        self._tick_request = None
        self._tick_thread = None
        self._tick_condition.notify_all()

    def _execute_one_complete_tick(self) -> None:
        with self._tick_condition:
            self._tick_number += 1
            self._tick_condition.notify_all()

    def _tick_breakpoint_triggered(self) -> bool:
        with self._tick_condition:
            breakpoints = list(self._tick_breakpoints)
            tick_number = self._tick_number

        for breakpoint in breakpoints:
            if breakpoint.kind == "at":
                if breakpoint.target == tick_number:
                    return True
                continue
            if breakpoint.kind == "when":
                assert breakpoint.condition is not None
                if self._evaluate_tick_break_condition(breakpoint.condition):
                    return True
                continue
            raise AssertionError(f"Unhandled tick breakpoint kind: {breakpoint.kind}")
        return False

    def _evaluate_tick_break_condition(self, expression: Expression) -> bool:
        value = self._evaluate(expression)
        if type(value) is bool:
            return value
        raise SproutRuntimeError(
            expression.line,
            expression.column,
            "Invalid tick breakpoint condition.",
            f"`tick.break when` needs a Boolean condition. Found: {type_name(value)}.",
        )

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
        if isinstance(expression, TickNumber):
            with self._tick_condition:
                return float(self._tick_number)
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
                    "Functions are not ordinary values in Sprout v0.3.",
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
                "Indexing only works with lists in Sprout v0.3.",
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
                "Lists can only be compared with `==` or `!=` in Sprout v0.3.",
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
                "Ordering comparisons only work with numbers in Sprout v0.3.",
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

    def _require_tick_rate(self, value: object, line: int, column: int) -> float:
        if type(value) is not float:
            raise SproutRuntimeError(
                line,
                column,
                "Invalid tick rate.",
                f"`tick.start(rate)` needs a number greater than 0. Found: {type_name(value)}.",
            )
        if value <= 0:
            raise SproutRuntimeError(
                line,
                column,
                "Invalid tick rate.",
                "`tick.start(rate)` needs a rate greater than 0 ticks per second.",
            )
        return value

    def _require_tick_count(self, value: object, line: int, column: int) -> int:
        if type(value) is not float:
            raise SproutRuntimeError(
                line,
                column,
                "Invalid tick count.",
                f"`tick.next(n)` needs a positive whole number. Found: {type_name(value)}.",
            )
        if not value.is_integer():
            raise SproutRuntimeError(
                line,
                column,
                "Invalid tick count.",
                "Use a positive whole number like 1, 2, or 10.",
            )
        if value <= 0:
            raise SproutRuntimeError(
                line,
                column,
                "Invalid tick count.",
                "`tick.next(n)` must run at least 1 tick.",
            )
        return int(value)

    def _require_tick_break_target(self, value: object, line: int, column: int) -> int:
        if type(value) is not float:
            raise SproutRuntimeError(
                line,
                column,
                "Invalid tick breakpoint target.",
                f"`tick.break at N` needs a positive whole number. Found: {type_name(value)}.",
            )
        if not value.is_integer():
            raise SproutRuntimeError(
                line,
                column,
                "Invalid tick breakpoint target.",
                "Use a whole tick number like 1, 2, or 30.",
            )
        if value <= 0:
            raise SproutRuntimeError(
                line,
                column,
                "Invalid tick breakpoint target.",
                "`tick.break at N` needs a tick number greater than 0.",
            )
        return int(value)

    def _require_tick_break_condition(self, expression: Expression) -> None:
        self._evaluate_tick_break_condition(expression)

    def _require_world_dimension(self, value: object, line: int, column: int, axis: str) -> int:
        if type(value) is not float:
            raise SproutRuntimeError(
                line,
                column,
                "Invalid world size.",
                f"World {axis} must be a positive whole number. Found: {type_name(value)}.",
            )
        if not value.is_integer():
            raise SproutRuntimeError(
                line,
                column,
                "Invalid world size.",
                f"World {axis} must be a whole number.",
            )
        if value <= 0:
            raise SproutRuntimeError(
                line,
                column,
                "Invalid world size.",
                f"World {axis} must be greater than 0.",
            )
        return int(value)

    def _require_world_coordinate(
        self,
        value: object,
        line: int,
        column: int,
        axis: str,
        world: WorldDefinition,
    ) -> float:
        if type(value) is not float:
            raise SproutRuntimeError(
                line,
                column,
                "Invalid world placement coordinate.",
                f"`{axis}` coordinate must be a number. Found: {type_name(value)}.",
            )
        if world.space_type == "grid" and not value.is_integer():
            raise SproutRuntimeError(
                line,
                column,
                "Invalid world placement coordinate.",
                "Grid world coordinates must be whole numbers.",
            )

        limit = world.width if axis == "x" else world.height
        if value < 0 or value >= limit:
            raise SproutRuntimeError(
                line,
                column,
                "World placement coordinate is out of bounds.",
                f"`{axis}` must be at least 0 and less than {limit}. Found: {format_value(value)}.",
            )
        return value

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
                "Negative list indexes are not supported in Sprout v0.3.",
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
            "Functions are not ordinary values in Sprout v0.3.",
            "Call the function by name instead of storing, printing, returning, or putting it in a list.",
        )
