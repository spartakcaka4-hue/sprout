import time
import unittest

from sprout import run_source
from sprout.errors import SproutError
from sprout.interpreter import Interpreter
from sprout.lexer import Lexer
from sprout.parser import Parser


def parse(source):
    return Parser(Lexer(source).lex()).parse()


def run_on(interpreter, source):
    return interpreter.run(parse(source))


def wait_until(predicate, timeout=1.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


class TickTests(unittest.TestCase):
    def error_message(self, source):
        with self.assertRaises(SproutError) as error:
            run_source(source)
        return error.exception.format()

    def stop_ticks(self, interpreter):
        try:
            run_on(interpreter, "tick.stop\n")
        except SproutError:
            pass

    def test_start_runs_automatic_ticks(self):
        interpreter = Interpreter()
        try:
            run_on(interpreter, "tick.start(100)\n")
            self.assertTrue(wait_until(lambda: interpreter.tick_number >= 2))
        finally:
            self.stop_ticks(interpreter)

    def test_pause_and_resume_use_remembered_rate(self):
        interpreter = Interpreter()
        try:
            run_on(interpreter, "tick.start(200)\n")
            self.assertTrue(wait_until(lambda: interpreter.tick_number >= 2))

            run_on(interpreter, "tick.pause\n")
            paused_at = interpreter.tick_number
            time.sleep(0.05)
            self.assertEqual(interpreter.tick_number, paused_at)

            run_on(interpreter, "tick.resume\n")
            self.assertTrue(wait_until(lambda: interpreter.tick_number > paused_at))
        finally:
            self.stop_ticks(interpreter)

    def test_next_runs_one_manual_tick(self):
        interpreter = Interpreter()
        run_on(interpreter, "tick.next()\n")
        self.assertEqual(interpreter.tick_number, 1)
        time.sleep(0.02)
        self.assertEqual(interpreter.tick_number, 1)

    def test_next_count_runs_exact_manual_ticks(self):
        interpreter = Interpreter()
        run_on(interpreter, "tick.next(4)\n")
        self.assertEqual(interpreter.tick_number, 4)

    def test_stop_ends_automatic_session_and_forgets_rate(self):
        interpreter = Interpreter()
        run_on(interpreter, "tick.start(200)\n")
        self.assertTrue(wait_until(lambda: interpreter.tick_number >= 2))

        run_on(interpreter, "tick.stop\n")
        stopped_at = interpreter.tick_number
        time.sleep(0.05)
        self.assertEqual(interpreter.tick_number, stopped_at)

        with self.assertRaises(SproutError) as error:
            run_on(interpreter, "tick.resume\n")
        self.assertIn("no paused automatic tick session", error.exception.format())

    def test_break_at_pauses_after_target_tick(self):
        interpreter = Interpreter()
        try:
            run_on(interpreter, "tick.break at 3\ntick.start(200)\n")
            self.assertTrue(wait_until(lambda: interpreter.tick_number == 3))
            time.sleep(0.05)
            self.assertEqual(interpreter.tick_number, 3)

            run_on(interpreter, "tick.resume\n")
            self.assertTrue(wait_until(lambda: interpreter.tick_number > 3))
        finally:
            self.stop_ticks(interpreter)

    def test_break_when_pauses_and_manual_next_ignores_breakpoints(self):
        interpreter = Interpreter()
        try:
            run_on(interpreter, "tick.break when tick.number >= 2\ntick.start(200)\n")
            self.assertTrue(wait_until(lambda: interpreter.tick_number == 2))
            time.sleep(0.05)
            self.assertEqual(interpreter.tick_number, 2)

            run_on(interpreter, "tick.next(2)\n")
            self.assertEqual(interpreter.tick_number, 4)
            time.sleep(0.05)
            self.assertEqual(interpreter.tick_number, 4)
        finally:
            self.stop_ticks(interpreter)

    def test_tick_number_starts_at_zero_and_only_completed_ticks_increment_it(self):
        interpreter = Interpreter()
        self.assertEqual(interpreter.tick_number, 0)
        with self.assertRaises(SproutError):
            run_on(interpreter, "tick.next(0)\n")
        self.assertEqual(interpreter.tick_number, 0)
        run_on(interpreter, "tick.next()\n")
        self.assertEqual(interpreter.tick_number, 1)
        self.assertEqual(run_source("print(tick.number)\ntick.next(2)\nprint(tick.number)\n"), "0\n2\n")

    def test_invalid_tick_arguments_raise_clear_errors(self):
        cases = [
            ("tick.start(0)", "Invalid tick rate."),
            ("tick.start(-1)", "Invalid tick rate."),
            ('tick.start("fast")', "Invalid tick rate."),
            ("tick.next(0)", "Invalid tick count."),
            ("tick.next(1.5)", "Invalid tick count."),
            ('tick.next("two")', "Invalid tick count."),
            ("tick.resume", "no paused automatic tick session"),
            ("tick.break at 0", "Invalid tick breakpoint target."),
            ("tick.break when 1", "Invalid tick breakpoint condition."),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                self.assertIn(message, self.error_message(source))

    def test_malformed_breakpoint_syntax_raises_clear_errors(self):
        cases = [
            ("tick.break", "Malformed tick breakpoint."),
            ("tick.break on 3", "Malformed tick breakpoint."),
            ("tick.break at", "Expected an expression after `tick.break at`."),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                self.assertIn(message, self.error_message(source))

    def test_existing_identifier_behavior_is_preserved(self):
        self.assertEqual(
            run_source(
                "tick = 5\n"
                "at = 1\n"
                "when = 2\n"
                "break = 3\n"
                "print(tick, at, when, break)\n"
            ),
            "5 1 2 3\n",
        )


if __name__ == "__main__":
    unittest.main()
