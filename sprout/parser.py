from __future__ import annotations

from .ast_nodes import (
    AgentDeclaration,
    AgentFieldDeclaration,
    AgentPresetSelection,
    Assignment,
    Attribute,
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
    MoveStatement,
    RemoveStatement,
    Statement,
    SpawnOverride,
    SpawnStatement,
    TickBreakStatement,
    TickNumber,
    TickStatement,
    Unary,
    Variable,
    WorldDeclaration,
    WorldPlacementDeclaration,
)
from .errors import SproutSyntaxError
from .lexer import Token, TokenType


COMPARISON_TOKENS = {
    TokenType.EQUAL_EQUAL,
    TokenType.BANG_EQUAL,
    TokenType.LESS,
    TokenType.LESS_EQUAL,
    TokenType.GREATER,
    TokenType.GREATER_EQUAL,
}

BUILTIN_NAMES = {"print", "length"}


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0
        self.block_depth = 0
        self.function_depth = 0

    def parse(self) -> Program:
        statements: list[Statement] = []
        while not self._is_at_end():
            if self._match(TokenType.NEWLINE):
                continue
            if self._check(TokenType.DEDENT):
                token = self._peek()
                raise SproutSyntaxError(
                    token.line,
                    token.column,
                    "Found a dedent with no matching block.",
                    "Check the indentation above this line.",
                )
            statements.append(self._statement())
        return Program(statements)

    def _statement(self) -> Statement:
        if self._is_environment_statement_start():
            return self._environment_declaration()
        if self._is_world_statement_start():
            return self._world_declaration()
        if self._is_place_statement_start():
            return self._placement_declaration()
        if self._is_agent_statement_start():
            return self._agent_declaration()
        if self._is_spawn_statement_start():
            return self._spawn_statement()
        if self._is_move_statement_start():
            return self._move_statement()
        if self._is_remove_statement_start():
            return self._remove_statement()
        if self._is_tick_statement_start():
            return self._tick_statement()
        if self._match(TokenType.IF):
            return self._if_statement(self._previous())
        if self._match(TokenType.REPEAT):
            return self._repeat_statement(self._previous())
        if self._match(TokenType.FOR):
            return self._for_statement(self._previous())
        if self._match(TokenType.FUNC):
            token = self._previous()
            if self.block_depth != 0:
                raise SproutSyntaxError(
                    token.line,
                    token.column,
                    "Function definitions are only allowed at the top level.",
                    "Move this `func` definition out of the block.",
                )
            return self._function_definition(token)
        if self._match(TokenType.RETURN):
            return self._return_statement(self._previous())
        if self._check(TokenType.ELSE):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "`else` can only appear directly after an `if` block.",
                "Check the indentation of this `else` line.",
            )
        return self._simple_statement()

    def _simple_statement(self) -> Statement:
        if self._check(TokenType.IDENTIFIER) and self._check_next(TokenType.EQUAL):
            name = self._advance()
            self._check_name_is_assignable(name)
            self._advance()
            value = self._expression()
            self._consume_statement_end()
            return Assignment(name.lexeme, value, name.line, name.column)

        expression = self._expression()
        if self._match(TokenType.EQUAL):
            token = self._previous()
            if isinstance(expression, Index):
                raise SproutSyntaxError(
                    token.line,
                    token.column,
                    "List item assignment is not supported in Sprout v0.4.",
                    "Create a new list value instead.",
                )
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Only plain variable names can be assigned with `=`.",
                "Use `==` when you want to compare two values.",
            )
        if not isinstance(expression, Call):
            raise SproutSyntaxError(
                expression.line,
                expression.column,
                "Only assignments and function calls can stand alone as statements.",
                "Assign this value to a name, pass it to a function, or remove the line.",
            )
        self._consume_statement_end()
        return ExpressionStatement(expression, expression.line, expression.column)

    def _if_statement(self, if_token: Token) -> IfStatement:
        condition = self._expression()
        body = self._block("if")
        branches = [(condition, body)]
        else_body: list[Statement] | None = None

        while self._match(TokenType.ELSE):
            else_token = self._previous()
            if self._match(TokenType.IF):
                condition = self._expression()
                branches.append((condition, self._block("else if")))
                continue
            if else_body is not None:
                raise SproutSyntaxError(
                    else_token.line,
                    else_token.column,
                    "An `if` chain can only have one `else` block.",
                )
            else_body = self._block("else")
            break

        return IfStatement(branches, else_body, if_token.line, if_token.column)

    def _repeat_statement(self, repeat_token: Token) -> RepeatStatement:
        count = self._expression()
        counter_name: str | None = None
        if self._match(TokenType.AS):
            name = self._consume(TokenType.IDENTIFIER, "Expected a counter name after `as`.")
            self._check_name_is_assignable(name)
            counter_name = name.lexeme
        body = self._block("repeat")
        return RepeatStatement(count, counter_name, body, repeat_token.line, repeat_token.column)

    def _for_statement(self, for_token: Token) -> ForStatement:
        name = self._consume(TokenType.IDENTIFIER, "Expected a loop variable name after `for`.")
        self._check_name_is_assignable(name)
        self._consume(TokenType.IN, "Expected `in` after the loop variable name.")
        iterable = self._expression()
        body = self._block("for")
        return ForStatement(name.lexeme, iterable, body, for_token.line, for_token.column)

    def _function_definition(self, func_token: Token) -> FunctionDef:
        name = self._consume(TokenType.IDENTIFIER, "Expected a function name after `func`.")
        self._check_name_is_assignable(name)
        self._consume(TokenType.LEFT_PAREN, "Expected `(` after the function name.")
        params: list[str] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                param = self._consume(TokenType.IDENTIFIER, "Expected a parameter name.")
                self._check_name_is_assignable(param)
                if param.lexeme in params:
                    raise SproutSyntaxError(
                        param.line,
                        param.column,
                        f"Parameter `{param.lexeme}` is listed more than once.",
                        "Use each parameter name only once.",
                    )
                params.append(param.lexeme)
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RIGHT_PAREN, "Expected `)` after the parameter list.")
        body = self._block("func", in_function=True)
        return FunctionDef(name.lexeme, params, body, func_token.line, func_token.column)

    def _return_statement(self, return_token: Token) -> ReturnStatement:
        if self.function_depth == 0:
            raise SproutSyntaxError(
                return_token.line,
                return_token.column,
                "`return` can only be used inside a function.",
            )
        if self._check(TokenType.NEWLINE) or self._check(TokenType.DEDENT) or self._check(TokenType.EOF):
            self._consume_statement_end()
            return ReturnStatement(None, return_token.line, return_token.column)
        value = self._expression()
        self._consume_statement_end()
        return ReturnStatement(value, return_token.line, return_token.column)

    def _environment_declaration(self) -> EnvironmentDeclaration:
        environment_token = self._advance()
        if self.block_depth != 0:
            raise SproutSyntaxError(
                environment_token.line,
                environment_token.column,
                "Environment declarations are only allowed at the top level.",
                "Move this `environment` declaration out of the block.",
            )

        name = self._consume(TokenType.IDENTIFIER, "Expected an environment name after `environment`.")
        self._check_name_is_assignable(name)
        environment_type = self._environment_body()
        return EnvironmentDeclaration(name.lexeme, environment_type, environment_token.line, environment_token.column)

    def _environment_body(self) -> str:
        self._consume_colon_after_header("environment")
        if not self._match(TokenType.NEWLINE):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Expected a new line after `:`.",
                "Put the environment type on the next line and indent it by 4 spaces.",
            )
        if not self._match(TokenType.INDENT):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Expected an indented block after `environment`.",
                "Write a type field like `type = ground` inside the environment block.",
            )

        environment_type: str | None = None
        self.block_depth += 1
        try:
            while not self._check(TokenType.DEDENT) and not self._check(TokenType.EOF):
                if self._match(TokenType.NEWLINE):
                    continue
                name = self._consume(TokenType.IDENTIFIER, "Expected `type = ground`, `type = water`, or `type = air`.")
                if name.lexeme != "type":
                    raise SproutSyntaxError(
                        name.line,
                        name.column,
                        "Environment declarations only support a `type` field.",
                        "Use `type = ground`, `type = water`, or `type = air`.",
                    )
                if environment_type is not None:
                    raise SproutSyntaxError(
                        name.line,
                        name.column,
                        "Environment declarations can only set `type` once.",
                    )
                self._consume(TokenType.EQUAL, "Expected `=` after `type`.")
                value = self._consume(TokenType.IDENTIFIER, "Expected an environment type name after `type =`.")
                environment_type = value.lexeme
                self._consume_statement_end()
        finally:
            self.block_depth -= 1

        if environment_type is None:
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Environment declarations need a type.",
                "Use `type = ground`, `type = water`, or `type = air`.",
            )
        self._consume(TokenType.DEDENT, "Expected the environment block to end with a matching dedent.")
        return environment_type

    def _world_declaration(self) -> WorldDeclaration:
        world_token = self._advance()
        if self.block_depth != 0:
            raise SproutSyntaxError(
                world_token.line,
                world_token.column,
                "World declarations are only allowed at the top level.",
                "Move this `world` declaration out of the block.",
            )

        name = self._consume(TokenType.IDENTIFIER, "Expected a world name after `world`.")
        self._check_name_is_assignable(name)
        fields = self._world_body()
        size_width, size_height, size_token = fields["size"]
        space_type, space_token = fields["space"]
        environment_name, environment_token = fields["environment"]
        return WorldDeclaration(
            name.lexeme,
            size_width,
            size_height,
            space_type,
            environment_name,
            world_token.line,
            world_token.column,
            size_token.line,
            size_token.column,
            space_token.line,
            space_token.column,
            environment_token.line,
            environment_token.column,
        )

    def _world_body(self) -> dict[str, object]:
        self._consume_colon_after_header("world")
        if not self._match(TokenType.NEWLINE):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Expected a new line after `:`.",
                "Put the world metadata on the next line and indent it by 4 spaces.",
            )
        if not self._match(TokenType.INDENT):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Expected an indented block after `world`.",
                "Write `size`, `space`, and `environment` fields inside the world block.",
            )

        fields: dict[str, object] = {}
        saw_item = False
        self.block_depth += 1
        try:
            while not self._check(TokenType.DEDENT) and not self._check(TokenType.EOF):
                if self._match(TokenType.NEWLINE):
                    continue
                saw_item = True
                self._world_body_item(fields)
        finally:
            self.block_depth -= 1

        if not saw_item:
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Empty world declarations are not supported in Sprout v0.4.",
                "Add `size`, `space`, and `environment` fields.",
            )

        for field_name in ("size", "space", "environment"):
            if field_name not in fields:
                token = self._peek()
                raise SproutSyntaxError(
                    token.line,
                    token.column,
                    f"World declaration is missing `{field_name}`.",
                )

        self._consume(TokenType.DEDENT, "Expected the world block to end with a matching dedent.")
        return fields

    def _world_body_item(self, fields: dict[str, object]) -> None:
        name = self._consume(TokenType.IDENTIFIER, "Expected a world field name.")
        if name.lexeme not in ("size", "space", "environment"):
            raise SproutSyntaxError(
                name.line,
                name.column,
                f"Unknown world field `{name.lexeme}`.",
                "World declarations only support `size`, `space`, and `environment`.",
            )
        if name.lexeme in fields:
            raise SproutSyntaxError(
                name.line,
                name.column,
                f"World declarations can only set `{name.lexeme}` once.",
            )
        self._consume(TokenType.EQUAL, f"Expected `=` after `{name.lexeme}`.")

        if name.lexeme == "size":
            width = self._expression()
            self._consume(TokenType.COMMA, "Expected `,` between world width and height.")
            height = self._expression()
            self._consume_statement_end()
            fields[name.lexeme] = (width, height, name)
            return

        if name.lexeme == "space":
            value = self._consume(TokenType.IDENTIFIER, "Expected a world space type after `space =`.")
            self._consume_statement_end()
            fields[name.lexeme] = (value.lexeme, value)
            return

        if name.lexeme == "environment":
            value = self._consume(TokenType.IDENTIFIER, "Expected an environment name after `environment =`.")
            self._consume_statement_end()
            fields[name.lexeme] = (value.lexeme, value)
            return

        raise AssertionError(f"Unhandled world field: {name.lexeme}")

    def _placement_declaration(self) -> PlacementDeclaration | WorldPlacementDeclaration:
        place = self._advance()
        agent_name = self._consume(TokenType.IDENTIFIER, "Expected an agent name after `place`.")
        self._consume(TokenType.IN, "Expected `in` after the agent name.")
        target_name = self._consume(TokenType.IDENTIFIER, "Expected an environment or world name after `in`.")
        if self._check(TokenType.IDENTIFIER) and self._peek().lexeme == "at":
            self._advance()
            x = self._expression()
            self._consume(TokenType.COMMA, "Expected `,` between placement coordinates.")
            y = self._expression()
            self._consume_statement_end()
            return WorldPlacementDeclaration(agent_name.lexeme, target_name.lexeme, x, y, place.line, place.column)
        self._consume_statement_end()
        return PlacementDeclaration(agent_name.lexeme, target_name.lexeme, place.line, place.column)

    def _spawn_statement(self) -> SpawnStatement:
        spawn = self._advance()
        agent_name = self._consume(TokenType.IDENTIFIER, "Expected an agent type after `spawn`.")

        instance_name: str | None = None
        if self._match(TokenType.AS):
            name = self._consume(TokenType.IDENTIFIER, "Expected an instance name after `as`.")
            self._check_name_is_assignable(name)
            instance_name = name.lexeme

        self._consume(TokenType.IN, "Expected `in` after the agent type or instance name.")
        world_name = self._consume(TokenType.IDENTIFIER, "Expected a world name after `in`.")
        at = self._consume_contextual_identifier("at", "Expected `at` before spawn coordinates.")
        x = self._expression()
        self._consume(TokenType.COMMA, "Expected `,` between spawn coordinates.")
        y = self._expression()

        overrides: list[SpawnOverride] = []
        if self._match(TokenType.COLON):
            overrides = self._spawn_override_block()
        else:
            self._consume_statement_end()

        return SpawnStatement(
            agent_name.lexeme,
            instance_name,
            world_name.lexeme,
            x,
            y,
            overrides,
            spawn.line,
            spawn.column,
        )

    def _spawn_override_block(self) -> list[SpawnOverride]:
        if not self._match(TokenType.NEWLINE):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Expected a new line after `:`.",
                "Put spawn field overrides on the next line and indent them by 4 spaces.",
            )
        if not self._match(TokenType.INDENT):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Expected an indented block after `spawn`.",
                "Indent field overrides like `energy = 70` by 4 spaces.",
            )

        overrides: list[SpawnOverride] = []
        self.block_depth += 1
        try:
            while not self._check(TokenType.DEDENT) and not self._check(TokenType.EOF):
                if self._match(TokenType.NEWLINE):
                    continue
                name = self._consume(TokenType.IDENTIFIER, "Expected a field name in the spawn override block.")
                self._consume(TokenType.EQUAL, f"Expected `=` after `{name.lexeme}`.")
                value = self._expression()
                self._consume_statement_end()
                overrides.append(SpawnOverride(name.lexeme, value, name.line, name.column))
        finally:
            self.block_depth -= 1

        if not overrides:
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Empty spawn override blocks are not supported.",
                "Remove the `:` or add at least one field override.",
            )
        self._consume(TokenType.DEDENT, "Expected the spawn override block to end with a matching dedent.")
        return overrides

    def _move_statement(self) -> MoveStatement:
        move = self._advance()
        target = self._consume(TokenType.IDENTIFIER, "Expected an agent instance name or `self` after `move`.")
        mode = self._consume(TokenType.IDENTIFIER, "Expected `by` or `to` after the move target.")
        if mode.lexeme not in ("by", "to"):
            raise SproutSyntaxError(
                mode.line,
                mode.column,
                "Expected `by` or `to` after the move target.",
                "Use `move self by dx, dy` or `move self to x, y`.",
            )
        x = self._expression()
        self._consume(TokenType.COMMA, "Expected `,` between movement coordinates.")
        y = self._expression()
        self._consume_statement_end()
        return MoveStatement(target.lexeme, mode.lexeme, x, y, move.line, move.column)

    def _remove_statement(self) -> RemoveStatement:
        remove = self._advance()
        target = self._consume(TokenType.IDENTIFIER, "Expected an agent instance name or `self` after `remove`.")
        self._consume_statement_end()
        return RemoveStatement(target.lexeme, remove.line, remove.column)

    def _agent_declaration(self) -> AgentDeclaration:
        agent_token = self._advance()
        if self.block_depth != 0:
            raise SproutSyntaxError(
                agent_token.line,
                agent_token.column,
                "Agent declarations are only allowed at the top level.",
                "Move this `agent` declaration out of the block.",
            )

        name = self._consume(TokenType.IDENTIFIER, "Expected an agent name after `agent`.")
        self._check_name_is_assignable(name)

        uses_presets = False
        if self._check(TokenType.IDENTIFIER) and self._peek().lexeme == "uses":
            self._advance()
            uses_presets = True

        presets, fields, every_tick_body = self._agent_body(uses_presets)
        return AgentDeclaration(
            name.lexeme,
            uses_presets,
            presets,
            fields,
            every_tick_body,
            agent_token.line,
            agent_token.column,
        )

    def _agent_body(
        self,
        uses_presets: bool,
    ) -> tuple[list[AgentPresetSelection], list[AgentFieldDeclaration], list[Statement] | None]:
        self._consume_colon_after_header("agent")
        if not self._match(TokenType.NEWLINE):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Expected a new line after `:`.",
                "Put the agent fields on the next line and indent them by 4 spaces.",
            )
        if not self._match(TokenType.INDENT):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Expected an indented block after `agent`.",
                "Indent the presets or fields that belong to this agent by 4 spaces.",
            )

        presets: list[AgentPresetSelection] = []
        fields: list[AgentFieldDeclaration] = []
        every_tick_body: list[Statement] | None = None
        self.block_depth += 1
        try:
            while not self._check(TokenType.DEDENT) and not self._check(TokenType.EOF):
                if self._match(TokenType.NEWLINE):
                    continue
                if self._is_every_tick_block_start():
                    every_token = self._advance()
                    self._advance()
                    if every_tick_body is not None:
                        raise SproutSyntaxError(
                            every_token.line,
                            every_token.column,
                            "Agent declarations can only define `every tick:` once.",
                            "Combine the tick behavior into one `every tick:` block.",
                        )
                    every_tick_body = self._block("every tick")
                    continue
                preset, field = self._agent_body_item(uses_presets)
                if preset is not None:
                    presets.append(preset)
                if field is not None:
                    fields.append(field)
        finally:
            self.block_depth -= 1

        if not presets and not fields and every_tick_body is None:
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Empty agent declarations are not supported in Sprout v0.4.",
                "Add at least one preset or custom field.",
            )
        self._consume(TokenType.DEDENT, "Expected the agent block to end with a matching dedent.")
        return presets, fields, every_tick_body

    def _agent_body_item(
        self,
        uses_presets: bool,
    ) -> tuple[AgentPresetSelection | None, AgentFieldDeclaration | None]:
        if self._check(TokenType.IDENTIFIER) and self._check_next(TokenType.DOT):
            category = self._advance()
            if not uses_presets:
                raise SproutSyntaxError(
                    category.line,
                    category.column,
                    "Agent presets require `uses` in the agent header.",
                    "Write `agent Name uses:` when selecting built-in presets.",
                )
            self._advance()
            preset = self._consume(TokenType.IDENTIFIER, "Expected a preset name after `.`.")
            self._consume_statement_end()
            return AgentPresetSelection(category.lexeme, preset.lexeme, category.line, category.column), None

        if self._check(TokenType.IDENTIFIER) and self._check_next(TokenType.EQUAL):
            name = self._advance()
            self._check_name_is_assignable(name)
            self._advance()
            value = self._expression()
            self._consume_statement_end()
            return None, AgentFieldDeclaration(name.lexeme, value, name.line, name.column)

        token = self._peek()
        raise SproutSyntaxError(
            token.line,
            token.column,
            "Agent declarations only support preset names and field assignments.",
            "Use `position.basic` or a field like `energy = 5`.",
        )

    def _block(self, header_kind: str, *, in_function: bool = False) -> list[Statement]:
        self._consume_colon_after_header(header_kind)
        if not self._match(TokenType.NEWLINE):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Expected a new line after `:`.",
                "Put the block body on the next line and indent it by 4 spaces.",
            )
        if not self._match(TokenType.INDENT):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                f"Expected an indented block after `{header_kind}`.",
                "Indent the code that belongs in this block by 4 spaces.",
            )

        statements: list[Statement] = []
        self.block_depth += 1
        if in_function:
            self.function_depth += 1
        try:
            while not self._check(TokenType.DEDENT) and not self._check(TokenType.EOF):
                if self._match(TokenType.NEWLINE):
                    continue
                statements.append(self._statement())
        finally:
            if in_function:
                self.function_depth -= 1
            self.block_depth -= 1

        if not statements:
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Empty blocks are not supported in Sprout v0.4.",
                "Add at least one statement inside the block.",
            )
        self._consume(TokenType.DEDENT, "Expected the block to end with a matching dedent.")
        return statements

    def _consume_colon_after_header(self, header_kind: str) -> None:
        if self._match(TokenType.COLON):
            return
        token = self._peek()
        if token.type == TokenType.EQUAL:
            raise SproutSyntaxError(
                token.line,
                token.column,
                "`=` assigns a value and cannot be used inside a condition.",
                "Use `==` when you want to compare two values.",
            )
        raise SproutSyntaxError(
            token.line,
            token.column,
            f"Expected `:` after `{header_kind}`.",
            "Add `:` at the end of the block header.",
        )

    def _expression(self) -> Expression:
        return self._or()

    def _or(self) -> Expression:
        expression = self._and()
        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._and()
            expression = Binary(expression, operator.type, operator.lexeme, right, operator.line, operator.column)
        return expression

    def _and(self) -> Expression:
        expression = self._comparison()
        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._comparison()
            expression = Binary(expression, operator.type, operator.lexeme, right, operator.line, operator.column)
        return expression

    def _comparison(self) -> Expression:
        expression = self._term()
        if self._match(TokenType.EXISTS):
            operator = self._previous()
            expression = Binary(
                expression,
                TokenType.BANG_EQUAL,
                "!=",
                Literal(None, "nothing", operator.line, operator.column),
                operator.line,
                operator.column,
            )
            if self._check(*COMPARISON_TOKENS, TokenType.EXISTS):
                raise SproutSyntaxError(
                    operator.line,
                    operator.column,
                    "Chained comparisons like `1 < x < 10` are not supported yet.",
                    "Use `1 < x and x < 10` instead.",
                )
        elif self._match(*COMPARISON_TOKENS):
            operator = self._previous()
            right = self._term()
            if self._check(*COMPARISON_TOKENS, TokenType.EXISTS):
                raise SproutSyntaxError(
                    operator.line,
                    operator.column,
                    "Chained comparisons like `1 < x < 10` are not supported yet.",
                    "Use `1 < x and x < 10` instead.",
                )
            expression = Binary(expression, operator.type, operator.lexeme, right, operator.line, operator.column)
        return expression

    def _term(self) -> Expression:
        expression = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            right = self._factor()
            expression = Binary(expression, operator.type, operator.lexeme, right, operator.line, operator.column)
        return expression

    def _factor(self) -> Expression:
        expression = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self._previous()
            right = self._unary()
            expression = Binary(expression, operator.type, operator.lexeme, right, operator.line, operator.column)
        return expression

    def _unary(self) -> Expression:
        if self._match(TokenType.NOT, TokenType.MINUS):
            operator = self._previous()
            operand = self._unary()
            return Unary(operator.type, operator.lexeme, operand, operator.line, operator.column)
        return self._call()

    def _call(self) -> Expression:
        expression = self._primary()
        while True:
            if self._match(TokenType.LEFT_PAREN):
                paren = self._previous()
                args: list[Expression] = []
                if not self._check(TokenType.RIGHT_PAREN):
                    while True:
                        args.append(self._expression())
                        if not self._match(TokenType.COMMA):
                            break
                self._consume(TokenType.RIGHT_PAREN, "Expected `)` after the arguments.")
                expression = Call(expression, args, expression.line, expression.column)
            elif self._match(TokenType.LEFT_BRACKET):
                bracket = self._previous()
                index = self._expression()
                self._consume(TokenType.RIGHT_BRACKET, "Expected `]` after the index.")
                expression = Index(expression, index, expression.line, expression.column)
            elif self._match(TokenType.DOT):
                dot = self._previous()
                name = self._consume(TokenType.IDENTIFIER, "Expected a field name after `.`.")
                expression = Attribute(expression, name.lexeme, dot.line, dot.column)
            else:
                break
        return expression

    def _primary(self) -> Expression:
        if self._match(TokenType.NUMBER):
            token = self._previous()
            return Literal(token.value, "number", token.line, token.column)
        if self._match(TokenType.TEXT):
            token = self._previous()
            return Literal(token.value, "text", token.line, token.column)
        if self._match(TokenType.BOOLEAN):
            token = self._previous()
            return Literal(token.value, "boolean", token.line, token.column)
        if self._match(TokenType.NOTHING):
            token = self._previous()
            return Literal(None, "nothing", token.line, token.column)
        if self._is_tick_number_expression():
            tick = self._advance()
            self._advance()
            self._advance()
            return TickNumber(tick.line, tick.column)
        if self._match(TokenType.IDENTIFIER):
            token = self._previous()
            return Variable(token.lexeme, token.line, token.column)
        if self._match(TokenType.LEFT_BRACKET):
            bracket = self._previous()
            elements: list[Expression] = []
            if not self._check(TokenType.RIGHT_BRACKET):
                while True:
                    elements.append(self._expression())
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RIGHT_BRACKET, "Expected `]` after the list items.")
            return ListLiteral(elements, bracket.line, bracket.column)
        if self._match(TokenType.LEFT_PAREN):
            expression = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected `)` after the grouped expression.")
            return expression

        token = self._peek()
        raise SproutSyntaxError(
            token.line,
            token.column,
            "Expected an expression.",
            None,
            found=token.lexeme or token.type.lower(),
            expected="a value, name, list, or grouped expression",
        )

    def _consume_statement_end(self) -> None:
        if self._match(TokenType.NEWLINE):
            return
        if self._check(TokenType.EOF) or self._check(TokenType.DEDENT):
            return
        token = self._peek()
        if token.type == TokenType.EQUAL:
            raise SproutSyntaxError(
                token.line,
                token.column,
                "`=` assigns a value and cannot appear here.",
                "Use `==` when you want to compare two values.",
            )
        raise SproutSyntaxError(
            token.line,
            token.column,
            "Expected the statement to end here.",
        )

    def _check_name_is_assignable(self, token: Token) -> None:
        if token.lexeme not in BUILTIN_NAMES:
            return
        raise SproutSyntaxError(
            token.line,
            token.column,
            f"`{token.lexeme}` is a built-in function name and cannot be reused.",
            "Choose a different name.",
        )

    def _consume(self, token_type: str, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        token = self._peek()
        raise SproutSyntaxError(token.line, token.column, message)

    def _consume_contextual_identifier(self, lexeme: str, message: str) -> Token:
        token = self._consume(TokenType.IDENTIFIER, message)
        if token.lexeme == lexeme:
            return token
        raise SproutSyntaxError(token.line, token.column, message)

    def _tick_statement(self) -> Statement:
        tick = self._consume_tick_name()
        self._consume(TokenType.DOT, "Expected `.` after `tick`.")
        member = self._consume(TokenType.IDENTIFIER, "Expected a tick command after `tick.`.")

        if member.lexeme == "start":
            self._consume(TokenType.LEFT_PAREN, "Expected `(` after `tick.start`.")
            rate = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected `)` after the tick rate.")
            self._consume_statement_end()
            return TickStatement("start", rate, tick.line, tick.column)

        if member.lexeme == "next":
            self._consume(TokenType.LEFT_PAREN, "Expected `(` after `tick.next`.")
            count: Expression | None = None
            if not self._check(TokenType.RIGHT_PAREN):
                count = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected `)` after the tick count.")
            self._consume_statement_end()
            return TickStatement("next", count, tick.line, tick.column)

        if member.lexeme in ("pause", "resume", "stop"):
            if self._check(TokenType.LEFT_PAREN):
                raise SproutSyntaxError(
                    member.line,
                    member.column,
                    f"`tick.{member.lexeme}` does not take parentheses.",
                    f"Write `tick.{member.lexeme}` on its own line.",
                )
            self._consume_statement_end()
            return TickStatement(member.lexeme, None, tick.line, tick.column)

        if member.lexeme == "break":
            return self._tick_break_statement(tick)

        if member.lexeme == "number":
            raise SproutSyntaxError(
                member.line,
                member.column,
                "`tick.number` can only be read as an expression.",
                "Use it in a call like `print(tick.number)`.",
            )

        raise SproutSyntaxError(
            member.line,
            member.column,
            f"Unknown tick command `tick.{member.lexeme}`.",
            "Use `tick.start(rate)`, `tick.pause`, `tick.resume`, `tick.next(...)`, `tick.stop`, or `tick.break ...`.",
        )

    def _tick_break_statement(self, tick: Token) -> TickBreakStatement:
        if not self._check(TokenType.IDENTIFIER):
            token = self._peek()
            raise SproutSyntaxError(
                token.line,
                token.column,
                "Malformed tick breakpoint.",
                "Use `tick.break at N` or `tick.break when condition`.",
            )

        kind = self._advance()
        if kind.lexeme not in ("at", "when"):
            raise SproutSyntaxError(
                kind.line,
                kind.column,
                "Malformed tick breakpoint.",
                "Use `tick.break at N` or `tick.break when condition`.",
            )
        if self._check(TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF):
            raise SproutSyntaxError(
                kind.line,
                kind.column,
                f"Expected an expression after `tick.break {kind.lexeme}`.",
            )

        condition = self._expression()
        self._consume_statement_end()
        return TickBreakStatement(kind.lexeme, condition, tick.line, tick.column)

    def _match(self, *types: str) -> bool:
        if self._check(*types):
            self._advance()
            return True
        return False

    def _check(self, *types: str) -> bool:
        if self._is_at_end() and TokenType.EOF not in types:
            return False
        return self._peek().type in types

    def _check_next(self, token_type: str) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == token_type

    def _is_environment_statement_start(self) -> bool:
        if not self._check(TokenType.IDENTIFIER):
            return False
        if self._peek().lexeme != "environment":
            return False
        return self._check_next(TokenType.IDENTIFIER)

    def _is_world_statement_start(self) -> bool:
        if not self._check(TokenType.IDENTIFIER):
            return False
        if self._peek().lexeme != "world":
            return False
        return self._check_next(TokenType.IDENTIFIER)

    def _is_place_statement_start(self) -> bool:
        if not self._check(TokenType.IDENTIFIER):
            return False
        if self._peek().lexeme != "place":
            return False
        return self._check_next(TokenType.IDENTIFIER)

    def _is_agent_statement_start(self) -> bool:
        if not self._check(TokenType.IDENTIFIER):
            return False
        if self._peek().lexeme != "agent":
            return False
        return self._check_next(TokenType.IDENTIFIER)

    def _is_spawn_statement_start(self) -> bool:
        if not self._check(TokenType.IDENTIFIER):
            return False
        if self._peek().lexeme != "spawn":
            return False
        return self._check_next(TokenType.IDENTIFIER)

    def _is_move_statement_start(self) -> bool:
        if not self._check(TokenType.IDENTIFIER):
            return False
        if self._peek().lexeme != "move":
            return False
        return self._check_next(TokenType.IDENTIFIER)

    def _is_remove_statement_start(self) -> bool:
        if not self._check(TokenType.IDENTIFIER):
            return False
        if self._peek().lexeme != "remove":
            return False
        return self._check_next(TokenType.IDENTIFIER)

    def _is_tick_statement_start(self) -> bool:
        if not self._check(TokenType.IDENTIFIER):
            return False
        if self._peek().lexeme != "tick":
            return False
        return self._check_next(TokenType.DOT)

    def _is_every_tick_block_start(self) -> bool:
        if self.current + 2 >= len(self.tokens):
            return False
        return (
            self.tokens[self.current].type == TokenType.IDENTIFIER
            and self.tokens[self.current].lexeme == "every"
            and self.tokens[self.current + 1].type == TokenType.IDENTIFIER
            and self.tokens[self.current + 1].lexeme == "tick"
            and self.tokens[self.current + 2].type == TokenType.COLON
        )

    def _is_tick_number_expression(self) -> bool:
        if self.current + 2 >= len(self.tokens):
            return False
        return (
            self.tokens[self.current].type == TokenType.IDENTIFIER
            and self.tokens[self.current].lexeme == "tick"
            and self.tokens[self.current + 1].type == TokenType.DOT
            and self.tokens[self.current + 2].type == TokenType.IDENTIFIER
            and self.tokens[self.current + 2].lexeme == "number"
        )

    def _consume_tick_name(self) -> Token:
        token = self._consume(TokenType.IDENTIFIER, "Expected `tick`.")
        if token.lexeme != "tick":
            raise SproutSyntaxError(token.line, token.column, "Expected `tick`.")
        return token

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]
