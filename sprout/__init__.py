from __future__ import annotations

from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser


__version__ = "0.4.1"


def run_source(source: str) -> str:
    tokens = Lexer(source).lex()
    program = Parser(tokens).parse()
    return Interpreter().run(program)
