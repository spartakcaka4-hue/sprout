import unittest

from sprout import run_source
from sprout.errors import SproutError


class InterpreterTests(unittest.TestCase):
    def error_message(self, source):
        with self.assertRaises(SproutError) as error:
            run_source(source)
        return error.exception.format()

    def test_prints_all_value_types(self):
        self.assertEqual(
            run_source('print(5.0, 0.5, "hi", true, false, nothing, [1, "two"])\n'),
            "5 0.5 hi true false nothing [1, two]\n",
        )

    def test_float_display_is_honest(self):
        self.assertEqual(run_source("print(0.1 + 0.2)\n"), "0.30000000000000004\n")

    def test_arithmetic_text_concat_and_precedence(self):
        self.assertEqual(run_source('print(2 + 3 * 4, (2 + 3) * 4, "a" + "b")\n'), "14 20 ab\n")

    def test_rejects_text_number_plus(self):
        message = self.error_message('print("Score: " + 10)')
        self.assertIn("Cannot combine text and number with `+`.", message)
        self.assertIn('Use `print("Score:", 10)`', message)

    def test_equality_rules_include_cross_type_and_lists(self):
        self.assertEqual(
            run_source(
                'print(5 == "5")\n'
                "print(0 == false)\n"
                "print(nothing == nothing)\n"
                "print([1, 2] == [1, 2])\n"
                "print([1, [2, 3]] == [1, [2, 3]])\n"
                'print([2] == ["2"])\n'
            ),
            "false\nfalse\ntrue\ntrue\ntrue\nfalse\n",
        )

    def test_list_ordering_is_rejected(self):
        message = self.error_message("print([1, 2] < [1, 3])")
        self.assertIn("Lists can only be compared with `==` or `!=`", message)

    def test_ordering_only_supports_numbers(self):
        self.assertEqual(run_source("print(2 < 3, 3 >= 3)\n"), "true true\n")
        message = self.error_message('print("a" < "b")')
        self.assertIn("Ordering comparisons only work with numbers", message)

    def test_conditions_must_be_booleans(self):
        message = self.error_message('if 1:\n    print("bad")\n')
        self.assertIn("Conditions must be Boolean values.", message)
        self.assertIn("score != 0", message)

    def test_and_or_not_require_booleans_and_short_circuit(self):
        self.assertEqual(
            run_source("print(false and (10 / 0 > 2))\nprint(true or (10 / 0 > 2))\n"),
            "false\ntrue\n",
        )
        self.assertIn("`and` needs Boolean values", self.error_message("print(5 and true)"))
        self.assertIn("`or` needs Boolean values", self.error_message("print(false or 5)"))
        self.assertIn("`not` needs a Boolean value", self.error_message("print(not 5)"))

    def test_repeat_counter_scope_and_zero_iteration_rules(self):
        self.assertEqual(run_source("repeat 3 as i:\n    print(i)\nprint(i)\n"), "0\n1\n2\n2\n")
        self.assertEqual(run_source("i = 99\nrepeat 0 as i:\n    print(i)\nprint(i)\n"), "99\n")
        message = self.error_message("repeat 0 as j:\n    print(j)\nprint(j)\n")
        self.assertIn("`j` is not defined.", message)

    def test_repeat_rejects_bad_counts(self):
        cases = [
            ('repeat "3":\n    print("x")', "`repeat` needs a number"),
            ('repeat 2.5:\n    print("x")', "whole number"),
            ('repeat -1:\n    print("x")', "cannot be negative"),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                self.assertIn(message, self.error_message(source))

    def test_for_loop_iteration_and_empty_list_rules(self):
        self.assertEqual(run_source("last = 9\nfor x in [1, 2]:\n    last = x\nprint(x, last)\n"), "2 2\n")
        self.assertEqual(run_source("x = 9\nfor x in []:\n    print(x)\nprint(x)\n"), "9\n")
        message = self.error_message("for item in []:\n    print(item)\nprint(item)\n")
        self.assertIn("`item` is not defined.", message)
        self.assertIn("`for ... in` needs a list", self.error_message('for n in "abc":\n    print(n)\n'))

    def test_length_and_indexing(self):
        self.assertEqual(
            run_source('foods = ["pizza", "apple"]\nprint(foods[0], length(foods), length("hi"))\n'),
            "pizza 2 2\n",
        )
        self.assertIn("Index 5 is out of range", self.error_message("items = [1, 2]\nprint(items[5])"))
        self.assertIn("Negative list indexes", self.error_message("items = [1]\nprint(items[-1])"))
        self.assertIn("whole numbers", self.error_message("items = [1]\nprint(items[0.5])"))
        self.assertIn("Indexing only works with lists", self.error_message('print("abc"[0])'))
        self.assertIn("`length` only works with text or lists", self.error_message("print(length(10))"))

    def test_functions_return_nothing_and_recurse(self):
        self.assertEqual(
            run_source(
                "func no_return():\n"
                '    print("side")\n'
                "\n"
                "func bare():\n"
                "    return\n"
                "\n"
                "func fact(n):\n"
                "    if n == 0:\n"
                "        return 1\n"
                "    else:\n"
                "        return n * fact(n - 1)\n"
                "\n"
                "print(no_return())\n"
                "print(bare())\n"
                "print(fact(5))\n"
            ),
            "side\nnothing\nnothing\n120\n",
        )

    def test_function_scoping_reads_globals_but_writes_locals(self):
        self.assertEqual(
            run_source(
                "x = 10\n"
                "func show_and_set():\n"
                "    print(x)\n"
                "    x = 5\n"
                "    print(x)\n"
                "\n"
                "show_and_set()\n"
                "print(x)\n"
            ),
            "10\n5\n10\n",
        )
        self.assertIn(
            "`local` is not defined.",
            self.error_message(
                "func make_local():\n"
                "    local = 1\n"
                "\n"
                "make_local()\n"
                "print(local)\n"
            ),
        )

    def test_function_call_order_and_argument_count(self):
        message = self.error_message('greet()\n\nfunc greet():\n    print("hello")\n')
        self.assertIn("`greet` is not defined.", message)
        self.assertEqual(run_source('func greet():\n    print("hello")\n\ngreet()\n'), "hello\n")
        self.assertIn(
            "`greet` expected 0 arguments but received 1",
            self.error_message('func greet():\n    print("hello")\n\ngreet(1)\n'),
        )

    def test_functions_are_not_ordinary_values(self):
        source = "func add(a, b):\n    return a + b\n\ncopy = add\n"
        self.assertIn("Functions are not ordinary values", self.error_message(source))
        self.assertIn("Functions are not ordinary values", self.error_message("print(print)\n"))

    def test_division_by_zero_and_undefined_variable_errors(self):
        self.assertIn("Division by zero.", self.error_message("print(10 / 0)"))
        self.assertIn("`total` is not defined.", self.error_message("print(total)"))


if __name__ == "__main__":
    unittest.main()
