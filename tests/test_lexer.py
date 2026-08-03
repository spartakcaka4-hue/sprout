import unittest

from sprout.errors import SproutSyntaxError
from sprout.lexer import Lexer, TokenType


def lex(source):
    return Lexer(source).lex()


def token_types(source):
    return [token.type for token in lex(source)]


class LexerTests(unittest.TestCase):
    def test_lexes_literals_keywords_symbols_and_comments(self):
        tokens = lex(
            'name = "Ada\\nLovelace" # comment\n'
            "score = 10.5\n"
            "flag = true and not false\n"
            "missing = nothing\n"
            "items = [1, 2]\n"
        )
        self.assertEqual(
            [token.type for token in tokens if token.type != TokenType.NEWLINE],
            [
                TokenType.IDENTIFIER,
                TokenType.EQUAL,
                TokenType.TEXT,
                TokenType.IDENTIFIER,
                TokenType.EQUAL,
                TokenType.NUMBER,
                TokenType.IDENTIFIER,
                TokenType.EQUAL,
                TokenType.BOOLEAN,
                TokenType.AND,
                TokenType.NOT,
                TokenType.BOOLEAN,
                TokenType.IDENTIFIER,
                TokenType.EQUAL,
                TokenType.NOTHING,
                TokenType.IDENTIFIER,
                TokenType.EQUAL,
                TokenType.LEFT_BRACKET,
                TokenType.NUMBER,
                TokenType.COMMA,
                TokenType.NUMBER,
                TokenType.RIGHT_BRACKET,
                TokenType.EOF,
            ],
        )
        self.assertEqual(tokens[2].value, "Ada\nLovelace")

    def test_lexes_indent_and_dedent_tokens(self):
        types = token_types('if true:\n    print("x")\nprint("done")\n')
        self.assertEqual(
            types,
            [
                TokenType.IF,
                TokenType.BOOLEAN,
                TokenType.COLON,
                TokenType.NEWLINE,
                TokenType.INDENT,
                TokenType.IDENTIFIER,
                TokenType.LEFT_PAREN,
                TokenType.TEXT,
                TokenType.RIGHT_PAREN,
                TokenType.NEWLINE,
                TokenType.DEDENT,
                TokenType.IDENTIFIER,
                TokenType.LEFT_PAREN,
                TokenType.TEXT,
                TokenType.RIGHT_PAREN,
                TokenType.NEWLINE,
                TokenType.EOF,
            ],
        )

    def test_rejects_invalid_numeric_literals(self):
        cases = [
            ("value = 007", "leading zeroes"),
            ("value = .5", "digit before the decimal point"),
            ("value = 5.", "digit after the decimal point"),
            ("value = 1_000", "Underscore digit separators"),
            ("value = 1e6", "Scientific notation"),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                with self.assertRaises(SproutSyntaxError) as error:
                    lex(source)
                self.assertIn(message, error.exception.format())

    def test_rejects_tabs_in_leading_whitespace(self):
        with self.assertRaises(SproutSyntaxError) as error:
            lex('if true:\n\tprint("x")')
        self.assertIn("Found a tab character in the indentation.", error.exception.format())

    def test_rejects_bad_indentation(self):
        cases = [
            ('if true:\n  print("x")', "exactly 4 spaces"),
            ('if true:\n        print("x")', "exactly 4 spaces more"),
            ('if true:\n    print("x")\n  print("bad")', "exactly 4 spaces"),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                with self.assertRaises(SproutSyntaxError) as error:
                    lex(source)
                self.assertIn(message, error.exception.format())

    def test_ignores_blank_and_comment_only_lines_inside_blocks(self):
        types = token_types('if true:\n\n    # comment\n    print("x")\n')
        self.assertIn(TokenType.INDENT, types)
        self.assertIn(TokenType.DEDENT, types)


if __name__ == "__main__":
    unittest.main()

