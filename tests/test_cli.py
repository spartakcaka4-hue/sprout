from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def run_cli_module(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "sprout.cli", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_success(self):
        result = self.run_cli_module("examples/hello_world.spr")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "Hello, world!\n")
        self.assertEqual(result.stderr, "")

    def test_missing_argument(self):
        result = self.run_cli_module()

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Usage: sprout path/to/program.spr", result.stderr)
        self.assertIn("missing .spr file path", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_too_many_arguments(self):
        result = self.run_cli_module("examples/hello_world.spr", "examples/functions.spr")

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Usage: sprout path/to/program.spr", result.stderr)
        self.assertIn("expected exactly one .spr file path", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_file(self):
        result = self.run_cli_module("missing.spr")

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("file not found", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_sprout_syntax_error_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            program = Path(directory) / "syntax_error.spr"
            program.write_text("return 5", encoding="utf-8")

            result = self.run_cli_module(str(program))

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("Line 1, column 1:", result.stderr)
        self.assertIn("`return` can only be used inside a function.", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_sprout_runtime_error_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            program = Path(directory) / "runtime_error.spr"
            program.write_text("print(total)", encoding="utf-8")

            result = self.run_cli_module(str(program))

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("Line 1, column 7:", result.stderr)
        self.assertIn("`total` is not defined.", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_python_sprout_py_compatibility(self):
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

    def test_project_script_entry_point_declared(self):
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(pyproject["project"]["scripts"]["sprout"], "sprout.cli:main")


if __name__ == "__main__":
    unittest.main()
