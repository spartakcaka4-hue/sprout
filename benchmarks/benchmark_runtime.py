from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import platform
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sprout.interpreter import Interpreter
from sprout.lexer import Lexer
from sprout.parser import Parser
from sprout.runtime import AgentInstance, WorldRuntime


MeasuredCallable = Callable[[], dict[str, object]]
PrepareCallable = Callable[[], MeasuredCallable]


@dataclass(frozen=True)
class Benchmark:
    name: str
    description: str
    agents: int
    ticks: int
    behavior_agents: int
    operation_count: int
    prepare: PrepareCallable


def parse_program(source: str):
    return Parser(Lexer(source).lex()).parse()


def run_program(source: str) -> Interpreter:
    interpreter = Interpreter()
    interpreter.run(parse_program(source))
    return interpreter


def make_grid_spawns(agent_name: str, world_name: str, count: int, *, spacing: int = 1) -> str:
    return "".join(
        f"spawn {agent_name} as a{i} in {world_name} at {i * spacing}, 0\n"
        for i in range(count)
    )


def idle_grid_source(count: int, ticks: int | None = None) -> str:
    return (
        "environment Land:\n"
        "    type = ground\n"
        "\n"
        "agent Idle uses:\n"
        "    position.cell\n"
        "    movement.none\n"
        "\n"
        "world Board:\n"
        f"    size = {count + 1}, 1\n"
        "    space = grid\n"
        "    environment = Land\n"
        "\n"
        + make_grid_spawns("Idle", "Board", count)
        + (f"tick.next({ticks})\n" if ticks is not None else "")
    )


def field_update_source(count: int, ticks: int | None = None) -> str:
    return (
        "environment Land:\n"
        "    type = ground\n"
        "\n"
        "agent Counter uses:\n"
        "    position.cell\n"
        "    movement.none\n"
        "    biology.energy\n"
        "\n"
        "    every tick:\n"
        "        energy = energy + 1\n"
        "\n"
        "world Board:\n"
        f"    size = {count + 1}, 1\n"
        "    space = grid\n"
        "    environment = Land\n"
        "\n"
        + make_grid_spawns("Counter", "Board", count)
        + (f"tick.next({ticks})\n" if ticks is not None else "")
    )


def grid_move_source(count: int, ticks: int, *, include_tick: bool = False) -> str:
    spacing = ticks + 2
    width = count * spacing + ticks + 1
    return (
        "environment Land:\n"
        "    type = ground\n"
        "\n"
        "agent Walker uses:\n"
        "    position.cell\n"
        "    movement.ground\n"
        "\n"
        "    every tick:\n"
        "        move self by 1, 0\n"
        "\n"
        "world Board:\n"
        f"    size = {width}, 1\n"
        "    space = grid\n"
        "    environment = Land\n"
        "\n"
        + make_grid_spawns("Walker", "Board", count, spacing=spacing)
        + (f"tick.next({ticks})\n" if include_tick else "")
    )


def mass_spawn_source(count: int) -> str:
    return (
        "environment Land:\n"
        "    type = ground\n"
        "\n"
        "agent Seed uses:\n"
        "    position.cell\n"
        "    movement.none\n"
        "    biology.energy\n"
        "\n"
        "world Board:\n"
        f"    size = {count + 1}, 1\n"
        "    space = grid\n"
        "    environment = Land\n"
        "\n"
        + make_grid_spawns("Seed", "Board", count)
    )


def mass_remove_setup_source(count: int) -> str:
    return mass_spawn_source(count)


def mass_remove_source(count: int) -> str:
    return "".join(f"remove a{i}\n" for i in range(count))


def continuous_setup_source(count: int) -> str:
    width = int(math.ceil(math.sqrt(count))) + 1
    lines = [
        "environment Land:",
        "    type = ground",
        "",
        "agent Dot uses:",
        "    position.continuous",
        "    movement.ground",
        "",
        "world Plane:",
        f"    size = {width}, {width}",
        "    space = continuous",
        "    environment = Land",
        "",
    ]
    for i in range(count):
        x = i % width
        y = i // width
        lines.append(f"spawn Dot as d{i} in Plane at {x}, {y}")
    return "\n".join(lines) + "\n"


def prepare_preparsed(source: str) -> PrepareCallable:
    program = parse_program(source)

    def prepare() -> MeasuredCallable:
        def run() -> dict[str, object]:
            interpreter = Interpreter()
            interpreter.run(program)
            return {"tick_number": interpreter.tick_number}

        return run

    return prepare


def prepare_program_operation(setup_source: str, operation_source: str) -> PrepareCallable:
    setup_program = parse_program(setup_source)
    operation_program = parse_program(operation_source)

    def prepare() -> MeasuredCallable:
        interpreter = Interpreter()
        interpreter.run(setup_program)

        def run() -> dict[str, object]:
            interpreter.run(operation_program)
            return {"tick_number": interpreter.tick_number}

        return run

    return prepare


def prepare_mass_removal(count: int) -> PrepareCallable:
    setup_program = parse_program(mass_remove_setup_source(count))
    remove_program = parse_program(mass_remove_source(count))

    def prepare() -> MeasuredCallable:
        interpreter = Interpreter()
        interpreter.run(setup_program)
        start_live = len(interpreter.worlds["Board"].agents)

        def run() -> dict[str, object]:
            interpreter.run(remove_program)
            remaining = len(interpreter.worlds["Board"].agents)
            return {"start_live_agents": start_live, "remaining_live_agents": remaining}

        return run

    return prepare


def prepare_occupied_lookup(count: int, lookups: int) -> PrepareCallable:
    setup_program = parse_program(mass_spawn_source(count))

    def prepare() -> MeasuredCallable:
        interpreter = Interpreter()
        interpreter.run(setup_program)
        world = interpreter.worlds["Board"]

        def run() -> dict[str, object]:
            hits = 0
            for i in range(lookups):
                if world.active_agent_at(float(i % count), 0.0) is not None:
                    hits += 1
            return {"lookups": lookups, "hits": hits}

        return run

    return prepare


def naive_nearby_agents(world: WorldRuntime, x: float, y: float, radius: float) -> list[AgentInstance]:
    radius_squared = radius * radius
    found: list[AgentInstance] = []
    for instance in world.agents.values():
        if not instance.active or instance.removed:
            continue
        dx = instance.x - x
        dy = instance.y - y
        if dx * dx + dy * dy <= radius_squared:
            found.append(instance)
    return found


def nearby_agents(world: WorldRuntime, x: float, y: float, radius: float) -> list[AgentInstance]:
    optimized = getattr(world, "nearby_agents", None)
    if optimized is not None:
        return list(optimized(x, y, radius))
    return naive_nearby_agents(world, x, y, radius)


def prepare_nearby_lookup(count: int, lookups: int, radius: float) -> PrepareCallable:
    setup_program = parse_program(continuous_setup_source(count))

    def prepare() -> MeasuredCallable:
        interpreter = Interpreter()
        interpreter.run(setup_program)
        world = interpreter.worlds["Plane"]
        width = world.width

        def run() -> dict[str, object]:
            total_found = 0
            for i in range(lookups):
                x = float(i % width)
                y = float((i // width) % width)
                total_found += len(nearby_agents(world, x, y, radius))
            return {"lookups": lookups, "total_found": total_found}

        return run

    return prepare


def make_benchmarks() -> list[Benchmark]:
    return [
        Benchmark(
            "idle_1k_agents_1k_ticks",
            "1,000 idle agents with no every tick block, 1,000 ticks",
            1_000,
            1_000,
            0,
            1_000 * 1_000,
            prepare_program_operation(idle_grid_source(1_000), "tick.next(1000)\n"),
        ),
        Benchmark(
            "idle_10k_agents_100_ticks",
            "10,000 idle agents with no every tick block, 100 ticks",
            10_000,
            100,
            0,
            10_000 * 100,
            prepare_program_operation(idle_grid_source(10_000), "tick.next(100)\n"),
        ),
        Benchmark(
            "field_update_10k_agents_100_ticks",
            "10,000 agents updating one field every tick, 100 ticks",
            10_000,
            100,
            10_000,
            10_000 * 100,
            prepare_program_operation(field_update_source(10_000), "tick.next(100)\n"),
        ),
        Benchmark(
            "grid_move_10k_agents_20_ticks",
            "10,000 grid agents moving every tick, 20 ticks",
            10_000,
            20,
            10_000,
            10_000 * 20,
            prepare_program_operation(grid_move_source(10_000, 20), "tick.next(20)\n"),
        ),
        Benchmark(
            "mass_spawn_20k_agents",
            "Mass spawning 20,000 grid agents",
            20_000,
            0,
            0,
            20_000,
            prepare_preparsed(mass_spawn_source(20_000)),
        ),
        Benchmark(
            "mass_remove_20k_agents",
            "Mass removal of 20,000 already-spawned grid agents",
            20_000,
            0,
            0,
            20_000,
            prepare_mass_removal(20_000),
        ),
        Benchmark(
            "occupied_cell_lookup_50k",
            "50,000 occupied-cell lookups in a 10,000-agent grid world",
            10_000,
            0,
            0,
            50_000,
            prepare_occupied_lookup(10_000, 50_000),
        ),
        Benchmark(
            "nearby_agent_lookup_200",
            "200 nearby-agent lookups in a 10,000-agent continuous world",
            10_000,
            0,
            0,
            200,
            prepare_nearby_lookup(10_000, 200, 1.5),
        ),
    ]


def total_memory_bytes() -> int | None:
    if platform.system() == "Windows":
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys)
        return None

    pages = os.sysconf_names.get("SC_PHYS_PAGES")
    page_size = os.sysconf_names.get("SC_PAGE_SIZE")
    if pages is not None and page_size is not None:
        return int(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
    return None


def process_memory_bytes() -> dict[str, int | None]:
    if platform.system() == "Windows":
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(ProcessMemoryCounters)
        process = ctypes.windll.kernel32.GetCurrentProcess()
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb)
        if ok:
            return {
                "working_set_bytes": int(counters.WorkingSetSize),
                "peak_working_set_bytes": int(counters.PeakWorkingSetSize),
            }
        return {"working_set_bytes": None, "peak_working_set_bytes": None}

    try:
        import resource
    except ImportError:
        return {"working_set_bytes": None, "peak_working_set_bytes": None}
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if platform.system() == "Darwin":
        peak_bytes = peak
    else:
        peak_bytes = peak * 1024
    return {"working_set_bytes": None, "peak_working_set_bytes": peak_bytes}


def machine_info() -> dict[str, object]:
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "total_memory_bytes": total_memory_bytes(),
    }


def measure(benchmark: Benchmark, repeat: int) -> dict[str, object]:
    runs: list[dict[str, object]] = []
    for _ in range(repeat):
        run = benchmark.prepare()
        memory_before = process_memory_bytes()
        start = time.perf_counter()
        extra = run()
        total_seconds = time.perf_counter() - start
        memory_after = process_memory_bytes()
        runs.append(
            {
                "total_seconds": total_seconds,
                "ticks_per_second": benchmark.ticks / total_seconds if benchmark.ticks else None,
                "agent_updates_per_second": (
                    (benchmark.behavior_agents * benchmark.ticks) / total_seconds
                    if benchmark.behavior_agents and benchmark.ticks
                    else None
                ),
                "operations_per_second": benchmark.operation_count / total_seconds,
                "working_set_before_bytes": memory_before["working_set_bytes"],
                "working_set_after_bytes": memory_after["working_set_bytes"],
                "peak_working_set_bytes": memory_after["peak_working_set_bytes"],
                "extra": extra,
            }
        )

    totals = [float(run["total_seconds"]) for run in runs]
    peaks = [
        int(run["peak_working_set_bytes"])
        for run in runs
        if run["peak_working_set_bytes"] is not None
    ]
    median_seconds = statistics.median(totals)
    return {
        "name": benchmark.name,
        "description": benchmark.description,
        "agents": benchmark.agents,
        "ticks": benchmark.ticks,
        "behavior_agents": benchmark.behavior_agents,
        "operation_count": benchmark.operation_count,
        "repeat": repeat,
        "median_total_seconds": median_seconds,
        "best_total_seconds": min(totals),
        "worst_total_seconds": max(totals),
        "ticks_per_second": benchmark.ticks / median_seconds if benchmark.ticks else None,
        "agent_updates_per_second": (
            (benchmark.behavior_agents * benchmark.ticks) / median_seconds
            if benchmark.behavior_agents and benchmark.ticks
            else None
        ),
        "operations_per_second": benchmark.operation_count / median_seconds,
        "peak_working_set_bytes": max(peaks) if peaks else None,
        "runs": runs,
    }


def write_report(path: Path, report: dict[str, object], *, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing benchmark report: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Sprout runtime benchmarks.")
    parser.add_argument("--output", type=Path, default=None, help="Write a JSON report to this path.")
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to run each benchmark.")
    parser.add_argument("--force", action="store_true", help="Allow overwriting an existing report.")
    args = parser.parse_args(argv)

    if args.repeat < 1:
        raise SystemExit("--repeat must be at least 1")

    benchmarks = make_benchmarks()
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "machine": machine_info(),
        "benchmarks": [measure(benchmark, args.repeat) for benchmark in benchmarks],
    }
    if args.output is not None:
        write_report(args.output, report, force=args.force)
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
