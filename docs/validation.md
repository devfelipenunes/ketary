# Experimental validation and production gate

## Runtime policy

Python 3.12.x is the sole development and CI target. Earlier dual-version CI results below are retained as historical evidence; Python 3.11 support is not maintained. Package metadata declares `>=3.12,<3.13` until the policy changes.

## Performance evidence

Commit ff866a14d1ed97678a29789fb2ca336a372afa79: [CI run](https://github.com/devfelipenunes/ketary/actions/runs/45731457342).
41 tests passed on Python 3.11 and 3.12. Qiskit 2.6.2.
20 paired repetitions after warmup, mixed gate workloads, shared Linux runner.

| Workload | Qiskit median (ms) | Ketary median (ms) | Overhead |
|---|---:|---:|---:|
| 8q, 1k gates build | 3.781 | 4.157 | 9.94% |
| 8q, 10k gates build | 37.498 | 41.013 | 9.37% |
| 8q, 128 gates simulation | 4.280 | 4.308 | 0.66% |
| 12q, 128 gates simulation | 7.001 | 7.047 | 0.65% |
| 16q, 64 gates simulation | 49.039 | 49.137 | 0.20% |

Median process peak RSS at 20q: native 161464 KiB; Ketary 161088 KiB.
Only three processes per variant and one memory workload. Do not interpret
the small difference as evidence that Ketary uses less memory in general.
Shared-runner absolute timings cannot be compared across runs. Re-run on
controlled hardware before a release; raw timings and p95 in CI artifacts.

## Current L0 baseline

[Main after PR #10](https://github.com/devfelipenunes/ketary/actions/runs/45737152433)
passed all CI jobs. [PR #10](https://github.com/devfelipenunes/ketary/actions/runs/45736946909)
recorded 201 tests and build overhead 9.25% / 8.78%, statevector overhead
0.02% / 0.86% / 0.53% for 8/12/16 qubits. Median peak RSS at 20q:
native 161400 KiB, wrapper 161292 KiB. Shared runner, limited workloads.

The documentation audit adds branch coverage reporting and supplemental
compose, export copy and trace measurements. These are diagnostic: native
trace returns arrays while Ketary additionally constructs validated snapshots.
No threshold is imposed on these operations before calibration. See
[audit](audit-l0.md) for remaining work.

## Usability protocol (not yet conducted with participants)

Run the two examples in a clean environment. These are automated functional
journeys, not a human usability study.

- Beginner: prepare a Bell state, obtain probabilities and explain why 00
  and 11 are the outcomes. Record time to first correct result, errors, help
  requests and whether instructions were understood.
- Intermediate: import a circuit with an extra Z gate, demonstrate identical
  Z-basis probabilities but different fidelity, locate the observed
  divergence against the explicit Bell reference, and export the circuit.
  Record task completion, time, errors and perceived clarity.

Compare equivalent Qiskit tasks with comparable instructions; counterbalance
task order where possible. Recruit volunteers with informed consent. Report
individual results and limitations, not general population conclusions.

## Gate

Technical validation: correct subset, tests, bounded memory, provisional
performance targets and reviewed contracts. Human usability, dependency
license review, vulnerability findings and owner review are separate.
The owner authorizes reviewed merges after CI. No package publication is authorized. Experimental L0 architecture is implemented; production and public release gates remain separate.
