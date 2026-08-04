from __future__ import annotations

import argparse
import cProfile
import io
import pstats
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark_runtime import make_benchmarks


def profile_benchmark(name_filter: str | None, output_dir: Path, limit: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_lines: list[str] = []
    for benchmark in make_benchmarks():
        if name_filter is not None and benchmark.name != name_filter:
            continue

        run = benchmark.prepare()
        profile = cProfile.Profile()
        profile.enable()
        extra = run()
        profile.disable()

        profile_path = output_dir / f"{benchmark.name}.prof"
        profile.dump_stats(str(profile_path))

        stream = io.StringIO()
        stats = pstats.Stats(profile, stream=stream).strip_dirs().sort_stats("cumulative")
        stats.print_stats(limit)
        summary_lines.append(f"# {benchmark.name}\n")
        summary_lines.append(f"extra={extra}\n")
        summary_lines.append(stream.getvalue())
        summary_lines.append("\n")

    if not summary_lines:
        raise SystemExit(f"No benchmark matched: {name_filter}")
    (output_dir / "summary.txt").write_text("".join(summary_lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Profile Sprout runtime benchmark operations.")
    parser.add_argument("--benchmark", default=None, help="Profile only one benchmark by name.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=30, help="Number of pstats rows per benchmark.")
    args = parser.parse_args(argv)

    profile_benchmark(args.benchmark, args.output_dir, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
