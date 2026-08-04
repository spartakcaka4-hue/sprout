# Sprout v0.4.1 Runtime Performance
This note records the measured performance work for the v0.4.1 runtime optimization release. v0.4.1 is intended to preserve v0.4 behavior while improving large-population runtime headroom.
## Methodology
- Benchmarks live in `benchmarks/benchmark_runtime.py` and are separate from the unit test suite.
- Sprout source is parsed before measured tick, removal, occupancy, and nearby-lookup operations where setup would otherwise obscure the operation being measured. Mass spawning measures the spawn program itself.
- Baseline report: `benchmark-results/baseline-v0.4.0-process-memory.json` (`repeat = 1`).
- Optimized report: `benchmark-results/optimized-v0.4.1-final.json` (`repeat = 3`, median shown).
- Profiling reports live under `benchmark-results/profiles/` and were captured with `cProfile`/`pstats` after benchmark setup.
- Memory columns use low-overhead process working-set snapshots where available.

## Captured Environment
- `python_version`: `3.14.3`
- `python_implementation`: `CPython`
- `platform`: `Windows-11-10.0.26200-SP0`
- `system`: `Windows`
- `release`: `11`
- `machine`: `AMD64`
- `processor`: `Intel64 Family 6 Model 142 Stepping 12, GenuineIntel`
- `cpu_count`: `8`
- `total_memory_bytes`: `16838545408`

## Results
| Benchmark | Baseline seconds | Optimized seconds | Change | Baseline ops/sec | Optimized ops/sec |
|---|---:|---:|---:|---:|---:|
| `idle_1k_agents_1k_ticks` | 0.264032 | 0.000797 | +33044.9% | 3787415 | 1255335167 |
| `idle_10k_agents_100_ticks` | 0.322769 | 0.000120 | +269548.1% | 3098193 | 8354218744 |
| `field_update_10k_agents_100_ticks` | 5.104303 | 3.360951 | +51.9% | 195913 | 297535 |
| `grid_move_10k_agents_20_ticks` | 2.246985 | 0.941638 | +138.6% | 89008 | 212396 |
| `mass_spawn_20k_agents` | 0.326324 | 0.181836 | +79.5% | 61289 | 109989 |
| `mass_remove_20k_agents` | 0.100880 | 0.048470 | +108.1% | 198256 | 412626 |
| `occupied_cell_lookup_50k` | 0.103047 | 0.034917 | +195.1% | 485214 | 1431959 |
| `nearby_agent_lookup_200` | 0.541356 | 0.001483 | +36404.1% | 369 | 134862 |

## Optimization Decisions
- Skipped idle agents in the tick loop by maintaining a spawn-order list of instances whose type actually defines `every tick:`. This directly addressed baseline profiles where idle ticks spent nearly all time resetting/visiting agents with no behavior.
- Cached static per-agent type data: field defaults, selected movement/position presets, and the presence of tick behavior. Spawn compatibility for a valid agent/world pair is cached after the first successful validation.
- Added internal named-instance lookup while preserving existing global-name behavior if a user overwrites the name.
- Kept grid occupancy as a direct coordinate-to-agent-id dictionary and tightened its hot lookup path.
- Added continuous-world spatial buckets and an internal `nearby_agents` method. This does not add public sensing syntax, but it prepares the v0.4.5 nearby-query work and removes the benchmark fallback full scan.
- Optimized movement happy paths for `move self` and literal numeric movement operands, and delayed construction of movement action strings until an error path actually needs them.
- Used slot-backed runtime dataclasses to reduce per-instance overhead.

## Considered And Skipped
- Slot/list-based field storage was not adopted. Field-update profiling still shows generic AST/name/assignment work as a bottleneck, but changing field storage would be a larger behavioral-risk surface than the measured v0.4.1 pass needs.
- A compact tick bytecode/execution-plan was not implemented. The AST is already parsed once and reused; deeper compilation is a better fit for a later focused release with stronger semantic validation.
- Multiprocessing, native extensions, GPU support, and new simulation behavior were intentionally out of scope.

## Remaining Bottlenecks
- `field_update_10k_agents_100_ticks` is still dominated by generic statement dispatch, AST evaluation, `_lookup`, and `_assign`. It improved from 195,913 ops/sec to 297,535 ops/sec, but this is the main remaining interpreter hot path.
- `grid_move_10k_agents_20_ticks` is still dominated by `_execute_move_statement`, coordinate validation, occupancy checks, and position updates. It improved from 89,008 ops/sec to 212,396 ops/sec.

## Behavior Protection
- The full unit test suite was run before optimization and after the final optimization: `python -m unittest discover -s tests` passed with 130 tests.
- The optimization keeps sequential spawn-order tick execution, existing movement/collision behavior, spawn/removal timing, public syntax, and existing user-facing errors intact.
