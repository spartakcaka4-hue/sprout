from __future__ import annotations

import sys
from pathlib import Path

from sprout import run_source
from sprout.errors import SproutError


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Usage: python sprout.py path/to/program.spr", file=sys.stderr)
        return 2

    path = Path(args[0])
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"Could not read {path}: {error}", file=sys.stderr)
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

