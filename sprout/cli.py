from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from . import run_source
from .errors import SproutError


def main(argv: Sequence[str] | None = None, *, program_name: str = "sprout") -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    usage = f"Usage: {program_name} path/to/program.spr"

    if not args:
        print(usage, file=sys.stderr)
        print("Error: missing .spr file path.", file=sys.stderr)
        return 2
    if len(args) > 1:
        print(usage, file=sys.stderr)
        print("Error: expected exactly one .spr file path.", file=sys.stderr)
        return 2

    path = Path(args[0])
    if path.suffix.lower() != ".spr":
        print(usage, file=sys.stderr)
        print("Error: expected a .spr file.", file=sys.stderr)
        return 2
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2
    if not path.is_file():
        print(f"Error: expected a file path: {path}", file=sys.stderr)
        return 2

    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"Error: could not read {path}: {error}", file=sys.stderr)
        return 2

    try:
        output = run_source(source)
    except SproutError as error:
        print(error.format(), file=sys.stderr)
        return 1

    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
