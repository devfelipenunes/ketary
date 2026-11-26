# BENCH04: comprehensive circuit performance matrix

The [historical scorecard](historical-performance-2026-11-26.md) is an
index of measured prior benchmarks, not a claim about current main.
This suite compares pre-PERF04–06 revision e995a5e with the current
candidate in separate Python 3.12 environments on the same runner.
The same script, inputs and pinned native versions are used; native
Qiskit is a control in each environment. Revision execution order is
counterbalanced. Three seeds per suite, 30 measured repetitions plus
three warmups per variant, randomized order within each trial.

## Workload families

- 36 authored algorithm cases: GHZ, QFT, graph state layers, QAOA,
  Ising/Trotter circuits, variational ansatz, BV, Simon, Grover and QPE.
- All 29 fixed gate specs plus MCX, at widths 8 and 12; 16 ordered
  random placements per gate case.
- 16 public QASMBench sources (pinned commit and blob checks).
  Nonterminal measurements and parser failures remain explicit
  exclusions; never count them as matched. Terminal readout and
  barriers are removed only for the named unitary projection.
- Actual local Aer GHZ shots and teleportation feedforward, at
  128/1024/8192 shots. Fixed seeded counts and analytic support.
  No dynamic QuEST path.

## Metrics and scope

Each case records original width, depth, gate count, multiwire count,
gate histogram, state bytes, input kind, compiler basis expansion and
lowered depth. Build, original execution (zero/complex), common-basis
execution, compiler lowering, native import and shots are separate.
Current common basis uses the explicit 11-gate QuEST whitelist.
Compare Qiskit Statevector, Ketary, Aer fusion on/off and QuEST
prepared/native-packing paths, plus the full lowering + QuEST path.
The latter includes compiler cost; the prepared paths do not.
The historical/current public API does not use QuEST by default.
No silent fallback. Results verify strict complex phase, normalization
and L2/max error; full operator when width <=8 and representation differs,
otherwise selected states. Exact circuit sequence equality is also recorded.
Report median, p95/p99, min/max, mean, standard deviation, MAD, individual
samples and paired ratios. CSV joins only matched stage/input/runner.
Independent RSS samples record absolute process high-water and prior
high-water (not live allocation or GPU VRAM). No timing assertions.

Run artifacts contain before/after JSON, comparison CSV, raw observations,
exclusions, exact revision, environment and CPU manifest. No results
should be claimed until the corresponding workflow completes. Dedicated
hardware and actual GPU measurements are still separate work.

## MCX synthesis regression

The first gate-matrix run exposed a strict operator mismatch after native HLS lowering of MCX in circuits with spectator wires. Qiskit's transpiler defaults to qubits_initially_zero=True; that assumption is not valid for arbitrary full-width complex input. The revised explicit lowering sets qubits_initially_zero=False (including corpus import normalization) and retains complete operator checks at width <=8. An occupied-spectator MCX preflight guards the same issue. No tolerance relaxation. Results from the rejected common-basis MCX path are not benchmark claims.
