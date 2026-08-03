from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import SproutSyntaxError


class TokenType:
    NUMBER = "NUMBER"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    NOTHING = "NOTHING"
    IDENTIFIER = "IDENTIFIER"

    IF = "IF"
    ELSE = "ELSE"
    REPEAT = "REPEAT"
    AS = "AS"
    FOR = "FOR"
    IN = "IN"
    FUNC = "FUNC"
    RETURN = "RETURN"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    EQUAL = "EQUAL"
    EQUAL_EQUAL = "EQUAL_EQUAL"
    BANG_EQUAL = "BANG_EQUAL"
    LESS = "LESS"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER = "GREATER"
    GREATER_EQUAL = "GREATER_EQUAL"
    LEFT_PAREN = "LEFT_PAREN"
    RIGHT_PAREN = "RIGHT_PAREN"
    LEFT_BRACKET = "LEFT_BRACKET"
    RIGHT_BRACKET = "RIGHT_BRACKET"
    COMMA = "COMMA"
    COLON = "COLON"
    NEWLINE = "NEWLINE"
    INDENT = "INDENT"
    DEDENT = "DEDENT"
    EOF = "EOF"


KEYWORDS = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "repeat": TokenType.REPEAT,
    "as": TokenType.AS,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "func": TokenType.FUNC,
    "return": TokenType.RETURN,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
}


@dataclass(frozen=True)
class Token:
    type: str
    lexeme: str
    value: Any
    line: int
    column: int


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source.replace("\r\n", "\n").replace("\r", "\n")
        self.tokens: list[Token] = []
        self.indents = [0]

    def lex(self) -> list[Token]:
        lines = self.source.split("\n")
        for line_number, line in enumerate(lines, start=1):
            if line_number == len(lines) and line == "" and self.source.endswith("\n"):
                continue
            self._lex_line(line, line_number)

        while len(self.indents) > 1:
            self.indents.pop()
            self.tokens.append(Token(TokenType.DEDENT, "", None, len(lines), 1))

        self.tokens.append(Token(TokenType.EOF, "", None, max(1, len(lines)), 1))
        return self.tokens

    def _lex_line(self, line: str, line_number: int) -> None:
        index = 0
        while index < len(line) and line[index] in (" ", "\t"):
            if line[index] == "\t":
                raise SproutSyntaxError(
                    line_number,
                    1,
                    "Found a tab character in the indentation.",
                    "Sprout uses spaces only. Replace tabs with 4 spaces per indentation level.",
                    found="tab",
                    expected="spaces",
                )
            index += 1

        if index == len(line) or line[index] == "#":
            return

        indent = index
        if indent % 4 != 0:
            raise SproutSyntaxError(
                line_number,
                indent + 1,
                "Indentation must use exactly 4 spaces per level.",
                "Adjust this line so its indentation is 0, 4, 8, or another multiple of 4 spaces.",
                found=f"{indent} spaces",
                expected="a multiple of 4 spaces",
            )

        current_indent = self.indents[-1]
        if indent > current_indent:
            if indent != current_indent + 4:
                raise SproutSyntaxError(
                    line_number,
                    1,
                    "A block body must be indented exactly 4 spaces more than its header.",
                    "Use one indentation level, which is exactly 4 spaces.",
                    found=f"{indent - current_indent} extra spaces",
                    expected="4 extra spaces",
                )
            self.indents.append(indent)
            self.tokens.append(Token(TokenType.INDENT, "", None, line_number, 1))
        elif indent < current_indent:
            while len(self.indents) > 1 and indent < self.indents[-1]:
                self.indents.pop()
                self.tokens.append(Token(TokenType.DEDENT, "", None, line_number, 1))
            if indent != self.indents[-1]:
                raise SproutSyntaxError(
                    line_number,
                    1,
                    "Dedenting must return to an earlier indentation level.",
                    "Align this line with an existing block level.",
                    found=f"{indent} spaces",
                    expected="an existing indentation level",
                )

        while index < len(line):
            char = line[index]
            column = index + 1
            if char == " ":
                index += 1
            elif char == "\t":
                raise SproutSyntaxError(
                    line_number,
                    column,
                    "Found a tab character.",
                    "Sprout uses spaces only. Replace tabs with spaces.",
                    found="tab",
                    expected="spaces",
                )
            elif char == "#":
                break
            elif char.isdigit():
                index = self._scan_number(line, line_number, index)
            elif char.isalpha() or char == "_":
                index = self._scan_identifier(line, line_number, index)
            elif char == '"':
                index = self._scan_text(line, line_number, index)
            elif char == "'":
                raise SproutSyntaxError(
                    line_number,
                    column,
                    "Text must use double quotes.",
                    'Use "like this" instead of single quotes.',
                    found="single quote",
                    expected="double quote",
                )
            elif char == "." and index + 1 < len(line) and line[index + 1].isdigit():
                raise SproutSyntaxError(
                    line_number,
                    column,
                    "Numbers need a digit before the decimal point.",
                    f"Write 0{line[index:self._number_tail_end(line, index + 1)]} instead.",
                    found="number without an integer part",
                    expected="a digit before the decimal point",
                )
            else:
                index = self._scan_symbol(line, line_number, index)

        self.tokens.append(Token(TokenType.NEWLINE, "", None, line_number, len(line) + 1))

    def _scan_number(self, line: str, line_number: int, index: int) -> int:
        start = index
        column = index + 1

        if line[index] == "0" and index + 1 < len(line) and line[index + 1].isdigit():
            end = index + 1
            while end < len(line) and line[end].isdigit():
                end += 1
            raise SproutSyntaxError(
                line_number,
                column,
                "Numbers cannot have leading zeroes.",
                f"Write {line[start:end].lstrip('0') or '0'} instead.",
                found=line[start:end],
                expected="a number without leading zeroes",
            )

        while index < len(line) and line[index].isdigit():
            index += 1

        if index < len(line) and line[index] == ".":
            if index + 1 >= len(line) or not line[index + 1].isdigit():
                raise SproutSyntaxError(
                    line_number,
                    column,
                    "Numbers need a digit after the decimal point.",
                    f"Write {line[start:index]}.0 instead.",
                    found=line[start : index + 1],
                    expected="digits after the decimal point",
                )
            index += 1
            while index < len(line) and line[index].isdigit():
                index += 1

        if index < len(line) and line[index] == "_":
            raise SproutSyntaxError(
                line_number,
                index + 1,
                "Underscore digit separators are not supported in Sprout v0.1.",
                "Write the digits without underscores.",
                found="_",
                expected="digits without separators",
            )
        if index < len(line) and line[index] in ("e", "E"):
            raise SproutSyntaxError(
                line_number,
                index + 1,
                "Scientific notation is not supported in Sprout v0.1.",
                "Write the full number instead.",
                found=line[index],
                expected="ordinary decimal digits",
            )
        if index < len(line) and (line[index].isalpha() or line[index] == "_"):
            raise SproutSyntaxError(
                line_number,
                index + 1,
                "A number cannot run directly into a name.",
                "Add an operator or space between the number and the name.",
                found=line[index],
                expected="an operator, comma, bracket, parenthesis, colon, or newline",
            )

        lexeme = line[start:index]
        self.tokens.append(Token(TokenType.NUMBER, lexeme, float(lexeme), line_number, column))
        return index

    def _number_tail_end(self, line: str, index: int) -> int:
        while index < len(line) and (line[index].isdigit() or line[index] == "."):
            index += 1
        return index

    def _scan_identifier(self, line: str, line_number: int, index: int) -> int:
        start = index
        while index < len(line) and (line[index].isalnum() or line[index] == "_"):
            index += 1
        lexeme = line[start:index]
        column = start + 1
        if lexeme == "true":
            self.tokens.append(Token(TokenType.BOOLEAN, lexeme, True, line_number, column))
        elif lexeme == "false":
            self.tokens.append(Token(TokenType.BOOLEAN, lexeme, False, line_number, column))
        elif lexeme == "nothing":
            self.tokens.append(Token(TokenType.NOTHING, lexeme, None, line_number, column))
        elif lexeme in KEYWORDS:
            self.tokens.append(Token(KEYWORDS[lexeme], lexeme, lexeme, line_number, column))
        else:
            self.tokens.append(Token(TokenType.IDENTIFIER, lexeme, lexeme, line_number, column))
        return index

    def _scan_text(self, line: str, line_number: int, index: int) -> int:
        start_column = index + 1
        index += 1
        chars: list[str] = []
        while index < len(line):
            char = line[index]
            if char == '"':
                lexeme = line[start_column - 1 : index + 1]
                self.tokens.append(Token(TokenType.TEXT, lexeme, "".join(chars), line_number, start_column))
                return index + 1
            if char == "\\":
                index += 1
                if index >= len(line):
                    raise SproutSyntaxError(
                        line_number,
                        start_column,
                        "Text literal is missing a closing quote.",
                        'Add " to end the text.',
                    )
                escape = line[index]
                escapes = {'"': '"', "\\": "\\", "n": "\n", "t": "\t"}
                if escape not in escapes:
                    raise SproutSyntaxError(
                        line_number,
                        index,
                        f"Unsupported escape sequence `\\{escape}`.",
                        'Use only \\", \\\\, \\n, or \\t in text.',
                        found=f"\\{escape}",
                        expected='\\", \\\\, \\n, or \\t',
                    )
                chars.append(escapes[escape])
            else:
                chars.append(char)
            index += 1

        raise SproutSyntaxError(
            line_number,
            start_column,
            "Text literal is missing a closing quote.",
            'Add " to end the text.',
            found="end of line",
            expected="closing quote",
        )

    def _scan_symbol(self, line: str, line_number: int, index: int) -> int:
        column = index + 1
        two_char = line[index : index + 2]
        two_char_tokens = {
            "==": TokenType.EQUAL_EQUAL,
            "!=": TokenType.BANG_EQUAL,
            "<=": TokenType.LESS_EQUAL,
            ">=": TokenType.GREATER_EQUAL,
        }
        if two_char in two_char_tokens:
            self.tokens.append(Token(two_char_tokens[two_char], two_char, two_char, line_number, column))
            return index + 2

        one_char_tokens = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "=": TokenType.EQUAL,
            "<": TokenType.LESS,
            ">": TokenType.GREATER,
            "(": TokenType.LEFT_PAREN,
            ")": TokenType.RIGHT_PAREN,
            "[": TokenType.LEFT_BRACKET,
            "]": TokenType.RIGHT_BRACKET,
            ",": TokenType.COMMA,
            ":": TokenType.COLON,
        }
        char = line[index]
        if char not in one_char_tokens:
            raise SproutSyntaxError(
                line_number,
                column,
                f"Unexpected character `{char}`.",
                None,
                found=char,
                expected="Sprout syntax",
            )
        self.tokens.append(Token(one_char_tokens[char], char, char, line_number, column))
        return index + 1

