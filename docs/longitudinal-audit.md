# Longitudinal audit — AUDIT02

Baseline: main after #49 and #51; Qiskit 2.6.2 is the authoritative native
reference, not an independent simulation backend. The existing shared-run
benchmark at #49 showed 12–13% construction overhead for simple scalar
gates, 0.4–0.7% statevector overhead at 8–16 qubits, and about 10x time
for repeated fluent batches of two H gates. The #48 writing comparison
had 254 Qiskit vs 404 Ketary lexical tokens on eight matched authored tasks.
Do not generalize these results to all tasks or human usability.

## Audit and prioritization

| Priority | Finding | Next experiment / acceptance |
|---|---|---|
| P0 | Repeated single-wire batch creates a new native staging circuit per call | Compare native, scalar SDK, grouped SDK; profile staging and validation; preserve atomicity |
| P0 | Pair placement syntax requires an explicit two-wire block and mappings | Compare scalar, apply_each, and native broadcasting; design explicit aligned pair extension to existing gates if justified |
| P0 | Native ansatz factories outperform current SDK source concision | Audit parameterized block composition and parameter vectors before introducing narrowly justified reusable templates |
| P1 | Dynamic grouped calls copy the full native prefix | Measure increasing readout/reset layers; keep late-failure atomicity and dynamic mode restrictions |
| P1 | Grouped math reuses terms but comparison must account for native deduplication | Compare ordinary native calls, native cache, scalar SDK, grouped SDK with identical results |
| P1 | Dense state width and replay limits differ | Separate state execution, construction, replay and verification; no inference that large construction is supported everywhere |
| P1 | Shared-run timing and authored token counts are weak usability evidence | Retain raw data and controlled host repetitions; held-out human/agent protocol, task time and correctness |

## Longitudinal experiment

Run three independent shared CI jobs, 30 randomized paired observations
per case after three warmups. Each uses the same deterministic workloads but
a different execution-order seed. The expanded matrix has 24 cases:
mixed construction up to 100,000 gates; repeated layers up to 100,000
gates; single-wire and pair placement scaling; measurement/reset
construction up to 1,024 operations; 8–20-qubit statevectors on the same
complex inputs; grouped Pauli queries (including native per-call cache).
Construction is compared using exact native circuit equality before
timing; numeric results are compared at 1e-9 with zero relative tolerance.
Gate counts, median, p95, extrema, raw timings, order, paired ratios, host
and dependency metadata are retained. Peak RSS is observed in separate
processes, not interpreted as isolated allocation size. Writing measurements
are separate: eight existing authored matched tasks and three additional
matched dynamic/topology tasks. No third-party code is executed.

Reproduce on an authorized isolated host using the pinned dependencies:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1
python research/longitudinal_benchmark.py --smoke --repetitions 3
for seed in 1101 2202 3303; do
  python research/longitudinal_benchmark.py --seed "$seed" --repetitions 30 > "longitudinal-$seed.json"
done
```

Keep failures and unfavorable outcomes; compare replicate medians and paired
ratios per case, not a single aggregate score. CI is diagnostic, not a
dedicated-host or publication gate. The study does not change runtime API.
The eventual optimization PRs must retain strict semantic oracles, resource
preflight, failure atomicity, type/stub parity and exact-head CI.
