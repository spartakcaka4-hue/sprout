from __future__ import annotations

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
                    "List item assignment is not supported in Sprout v0.1.",
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
                "Empty blocks are not supported in Sprout v0.1.",
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
        if self._match(*COMPARISON_TOKENS):
            operator = self._previous()
            right = self._term()
            if self._check(*COMPARISON_TOKENS):
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
