import unittest
from pathlib import Path

from sprout import run_source
from sprout.errors import SproutError


SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots" / "errors"


CASES = {
    "undefined_variable": "print(total)",
    "text_number_plus": 'print("Score: " + 10)',
    "return_outside_function": "return 5",
    "division_by_zero": "print(10 / 0)",
    "wrong_argument_count": "func add(a, b):\n    return a + b\n\nadd(1)",
    "index_out_of_range": "items = [1, 2]\nprint(items[5])",
    "chained_comparison": "print(1 < 2 < 3)",
    "tab_indentation": 'if true:\n\tprint("x")',
    "missing_block": 'if true:\nprint("x")',
}


class ErrorSnapshotTests(unittest.TestCase):
    def test_error_message_snapshots(self):
        for name, source in CASES.items():
            with self.subTest(name=name):
                with self.assertRaises(SproutError) as error:
                    run_source(source)
                expected = (SNAPSHOT_DIR / f"{name}.txt").read_text(encoding="utf-8").strip()
                self.assertEqual(error.exception.format(), expected)


if __name__ == "__main__":
    unittest.main()

