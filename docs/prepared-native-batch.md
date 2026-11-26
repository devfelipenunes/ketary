# PERF14–18 / AUD11: prepared CPU batch research

## BENCH06: completed BENCH04 evidence

Source: https://github.com/devfelipenunes/ketary/actions/runs/45764869707
Exact candidate 064935065d3194f39cd0819bd1e75c9bab4f295b.
Each cell is the upper median of case-level median-latency ratios against
Qiskit Statevector on that same runner, not a pooled host measurement.
Common-basis gate cases (60 per runner):

| Variant | 1101 | 2202 | 3303 |
|---|---:|---:|---:|
| Ketary | 1.043 | 1.044 | 1.037 |
| Aer prepared | 1.072 | 1.079 | 0.888 |
| QuEST prepared | 0.309 | 0.307 | 0.227 |
| QuEST Rust pack | 0.314 | 0.312 | 0.232 |
| QuEST including lowering | 2.117 | 2.187 | 1.787 |
| Ketary import / native copy | 7.866 | 8.256 | 8.099 |

The import comparison is validation versus copy, not identical work.
Corpus unitary projections (12 cases per runner):

| Variant | 1101 | 2202 | 3303 |
|---|---:|---:|---:|
| Ketary | 1.027 | 1.042 | 1.030 |
| Aer prepared | 0.766 | 0.939 | 0.752 |
| QuEST prepared | 0.213 | 0.297 | 0.209 |
| QuEST Rust pack | 0.220 | 0.315 | 0.222 |
| QuEST including lowering | 1.773 | 2.633 | 1.660 |

Sources: gate jobs 139723250269, 139723250228, 139723250193;
corpus jobs 139723250388, 139723250355, 139723249825. These six jobs
completed successfully. Algorithm jobs were still running at extraction.
No dedicated host or public speed claim. BENCH04 artifacts retain p95 and
raw observations; these log-derived summaries are a partial diagnostic.

## Experimental design

- PERF14: one FFI call for a batch rather than one call per state; Rust
  traversal prepares an immutable topology and ordered angle slots.
- PERF15: one QuEST CPU register is allocated per batch, overwritten from
  the same explicit input for every row, and destroyed before returning.
  No persistent global circuit or register cache.
- PERF16: adjacent identical involutions cancel, same-axis rotation angles
  add without modulo reduction; no gate reordering or general matrix fusion.
  Bounded-angle fusion is experimental and must satisfy strict native oracles.
- PERF17: same-host portable and -march=native builds, host cache/ISA
  manifest, widths 4/8/12/16 and output/topology/angle byte counts, stage
  timings. This is not evidence of actual SIMD instructions, cache misses,
  peak bandwidth or GPU acceleration. Hardware counters and disassembly
  require separate measurement.
- PERF18: explicit rows in native parameter order, repeated direct angle
  references supported. Arbitrary symbolic expressions and symbolic global
  phase rejected. General lowering remains an explicit separate operation.

Public Qiskit-based SDK remains unchanged. No second authoritative IR:
the packed program is a private immutable research snapshot, not a mutable
circuit model. No implicit execution, automatic fallback or publication.

## Resource and correctness contracts

Width 1..22, at most 100,000 operations and 256 rows. Output state payload
at most 128 MiB, angle table at most 64 MiB, before materialization; these
are not whole-process RSS limits. CPU register holds one dense state.
Calls are serialized by the existing environment lock. Caller must not
mutate borrowed execution buffers during a call. Fresh output arrays,
read-only bytes-backed prepared topology; no reuse across returned outputs.
Only 11 native gate types. Strict complex amplitude comparison (including
global phase and arbitrary initial states) at absolute 1e-9, no relaxation.
Full basis checks for small fusion and direct-parameter cases, rejected
unsupported gates, malformed rows, ownership and directionality checks.

Benchmarks compare equivalent arrays from native Qiskit, repeated QuEST,
batch QuEST, preparation-inclusive execution, native binding-inclusive
execution and fixed-program fused paths. Report native allocation, input,
kernel, export and destruction separately from Python wall time, with raw
repetitions and paired ratios. The preparation-inclusive variant is the
appropriate comparison for one-off execution; repeated prepared execution
must disclose preparation excluded. No timing thresholds in CI.
