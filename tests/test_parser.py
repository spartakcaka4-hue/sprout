import unittest

from sprout.ast_nodes import Binary, FunctionDef, IfStatement, Literal, RepeatStatement
from sprout.errors import SproutSyntaxError
from sprout.lexer import Lexer
from sprout.parser import Parser


def parse(source):
    return Parser(Lexer(source).lex()).parse()


class ParserTests(unittest.TestCase):
    def syntax_error(self, source):
        with self.assertRaises(SproutSyntaxError) as error:
            parse(source)
        return error.exception.format()

    def test_parses_if_else_if_else_chain(self):
        program = parse(
            "if score >= 90:\n"
            '    print("A")\n'
            "else if score >= 80:\n"
            '    print("B")\n'
            "else:\n"
            '    print("C")\n'
        )
        statement = program.statements[0]
        self.assertIsInstance(statement, IfStatement)
        self.assertEqual(len(statement.branches), 2)
        self.assertIsNotNone(statement.else_body)

    def test_parses_repeat_with_counter(self):
        program = parse('repeat 3 as i:\n    print("Lap", i)\n')
        statement = program.statements[0]
        self.assertIsInstance(statement, RepeatStatement)
        self.assertEqual(statement.counter_name, "i")

    def test_desugars_exists_to_not_equal_nothing(self):
        program = parse("answer = winner exists\n")
        expression = program.statements[0].value
        self.assertIsInstance(expression, Binary)
        self.assertEqual(expression.operator_type, "BANG_EQUAL")
        self.assertEqual(expression.operator_lexeme, "!=")
        self.assertIsInstance(expression.right, Literal)
        self.assertEqual(expression.right.literal_type, "nothing")

    def test_parses_top_level_function_definition(self):
        program = parse("func add(a, b):\n    return a + b\n")
        statement = program.statements[0]
        self.assertIsInstance(statement, FunctionDef)
        self.assertEqual(statement.name, "add")
        self.assertEqual(statement.params, ["a", "b"])

    def test_rejects_chained_comparisons(self):
        message = self.syntax_error("print(1 < x < 10)")
        self.assertIn("Chained comparisons", message)
        self.assertIn("1 < x and x < 10", message)

    def test_rejects_chaining_after_exists(self):
        message = self.syntax_error("print(winner exists == true)")
        self.assertIn("Chained comparisons", message)

    def test_rejects_return_outside_function(self):
        message = self.syntax_error("return 5")
        self.assertIn("`return` can only be used inside a function.", message)

    def test_rejects_nested_function_definitions(self):
        message = self.syntax_error('if true:\n    func inner():\n        print("x")\n')
        self.assertIn("Function definitions are only allowed at the top level.", message)

    def test_rejects_missing_indented_block(self):
        message = self.syntax_error('if true:\nprint("x")')
        self.assertIn("Expected an indented block", message)

    def test_rejects_list_item_assignment(self):
        message = self.syntax_error('foods = ["pizza"]\nfoods[0] = "sushi"\n')
        self.assertIn("List item assignment is not supported", message)

    def test_rejects_standalone_non_call_expression(self):
        message = self.syntax_error("1 + 2")
        self.assertIn("Only assignments and function calls can stand alone", message)

    def test_rejects_duplicate_parameter_names(self):
        message = self.syntax_error("func bad(x, x):\n    return x\n")
        self.assertIn("listed more than once", message)

    def test_rejects_reusing_builtin_names(self):
        cases = [
            "print = 5\n",
            "func length(value):\n    return value\n",
            "repeat 2 as print:\n    length([1])\n",
            "for length in [1]:\n    print(length)\n",
            "func bad(print):\n    return print\n",
        ]
        for source in cases:
            with self.subTest(source=source):
                self.assertIn("built-in function name", self.syntax_error(source))


if __name__ == "__main__":
    unittest.main()
