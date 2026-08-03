import subprocess
import sys
import unittest
from pathlib import Path

from sprout import run_source


ROOT = Path(__file__).resolve().parents[1]


EXAMPLES = {
    "hello_world.spr": "Hello, world!\n",
    "scores.spr": "You win\n",
    "loops.spr": "Lap 0\nLap 1\nLap 2\n",
    "lists.spr": "pizza\napple\nbread\n3\n",
    "functions.spr": "Sum: 5\n",
    "classify.spr": "95 -> A\n82 -> B\n61 -> C\n",
}


class ExampleTests(unittest.TestCase):
    def test_example_programs_match_expected_output(self):
        for filename, expected in EXAMPLES.items():
            with self.subTest(filename=filename):
                source = (ROOT / "examples" / filename).read_text(encoding="utf-8")
                self.assertEqual(run_source(source), expected)

    def test_cli_runs_example_program(self):
        result = subprocess.run(
            [sys.executable, "sprout.py", "examples/functions.spr"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "Sum: 5\n")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()

