# QContract: value, comparative evidence and recursive improvement plan (B1)

## Product hypothesis

An SDK-independent specification and verification layer for quantum
software, currently with a Qiskit adapter. Not a replacement for Qiskit
compilation, hardware execution or general-purpose simulation. Target
users: maintainers of quantum libraries, compiler passes, reversible
oracles/ancilla-heavy routines, fault-tolerance researchers and CI teams.
The product value is precise property checking, actionable counterexamples,
honest inconclusive status and repeatable evidence. Adoption and scientific
novelty are unproven.

## Prior art and best available competitors

- Quantum Hoare logic: https://doi.org/10.1145/2049706.2049708
- Design by Contract for Quantum Software: https://arxiv.org/abs/2303.17750
- QBricks, parametric deductive verification:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7984546/
- Quantum Correctness by Construction: https://doi.org/10.1145/3720433
- Hoare meets Heisenberg (particularly close to signed-Pauli reasoning):
  https://doi.org/10.22331/q-2026-07-23-2172
- Proq runtime statistical/projective assertions:
  https://doi.org/10.1145/3428218
- LintQ static analysis: https://doi.org/10.1145/3660802
- Qiskit PauliList: https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.quantum_info.PauliList
- Qiskit StabilizerState:
  https://quantum.cloud.ibm.com/docs/en/api/qiskit/2.5/qiskit.quantum_info.StabilizerState
- Qiskit Aer simulation methods: https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator
- Qiskit pauli-prop Rust package:
  https://qiskit.github.io/pauli-prop/
- MQT QCEC portfolio: https://mqt.readthedocs.io/projects/qcec/en/stable/equivalence_checking.html

The ingredients are established. No claim of the first quantum contract
system, first Pauli propagation algorithm, first adaptive verifier or
formal proof of the entire implementation. Investigate a *combined
engineering contribution*: exact restricted contracts, bounded
multi-method dispatch, witnesses and independently replayable evidence,
with low-friction SDK integration and a reproducible held-out benchmark.

## A4 evidence (verified original artifact data)

Candidate ee3699a5fa79377ecae08ef29be08921b675c501, run 46078771325.
Linux artifact 15235309347, macOS 15235499680; Qiskit 2.6.2, CPython 3.12.
Each: 55 smoke checks, 8978 dispatch parity checks, 1040 matched Clifford
verdicts; 32 benchmark scenarios, seven interleaved repetitions.
These are comparisons, not unique independent mathematical proofs.
Windows and broad CI still pending at time of review.

| Scope | Linux median speedup | macOS median speedup | Wins per host |
|---|---:|---:|---:|
| Prepared Boolean verdicts (QContract full report path vs Qiskit frame h) | 8.85 | 7.23 | 28/32 |
| Individual prepared query | 26.27 | 21.37 | 16/16 |
| 64 prepared queries | 2.82 | 2.11 | 12/16 |
| End to end (source circuit and already-built query specs) | 4.12 | 4.68 | 32/32 |

All four losses per host are the 4-wire/64-query cases. Worst observed
macOS case 0.593583 ms QContract vs 0.381875 ms Qiskit, 4 wires/256
gates/sparse. Linux 1.080597 vs 0.845607 ms for the same fixture.
QContract produces witness and identity metadata even when only a
Boolean is requested. Do not infer bottleneck shares from timing
alone. Profile per-spec hashing, admission, compact witness expansion,
allocation and FFI separately. End-to-end includes engine preparation
but not creation of the source circuit/specs. Qiskit frame h may
recompute inverse; test cached inverse frame s before claiming a robust
advantage over best available Qiskit.

R32 state artifact 15227253246: 80 exact expectations matched dense
numerical reference. Prepared dense Qiskit beat full native reports
in six of ten scenarios; native reports won at 16 and 20 wires in both
families. 20-wire random brickwork: 2.268672 ms native reports vs
8.469506 ms prepared statevector and 723.613429 ms dense end-to-end.
Do not use the exponential statevector baseline alone for Clifford:
StabilizerState and inverse tableau avoid that cost.
R32 equivalence artifact 15226789582: 16 simple appended-inverse/mutant
pairs agreed with QCEC; unequal setup and simple corpus limit claims.
No general speed superiority over QCEC.

## Recursive benchmark roadmap

| Round | Workloads and comparison | Output/gate |
|---|---|---|
| B1 (implemented, CI pending) | 144 prepared Clifford scenarios vs cached inverse; 10 state scenarios vs StabilizerState and inverse; 30 near-Clifford scenarios vs Rust pauli-prop | Correctness, coverage, cold/warm costs, median/p95, raw samples |
| B2 | Profile worst B1 cases; test compact or optional diagnostic output and batched state tableau expectation | Preserve all verdicts, witnesses when requested, budgets and independent replay; same-host A/B; reject regressions |
| B3 | Entangled/non-Clifford circuits, T-count/depth sweep, sparse support, connected/disconnected topologies; Aer MPS/extended-stabilizer | Match numeric accuracy, exact coverage, cap/timeouts, process peak RSS; record inconclusive cases |
| B4 | QCEC and Qiskit transpilation equivalence, compute-uncompute, Toffoli arithmetic/oracles, ancilla leakage; public held-out circuits | Detection rate for genuine semantic mutants, equivalent rewrites, false verdicts; compare prepare/verify total |
| B5 | Noise, measurement, QEC and rational coefficients; compare only matching admitted semantics | Exact/noise assumptions explicit; unsupported domain never called incorrect |
| B6 | Dedicated CPU, fixed versions, affinity, single/multiple threads, independent repeatability | Report uncertainty, memory/time curves and raw results; held-out fixtures not tuning set |
| B7 | Developer study: CI integration in real Qiskit projects; baseline pytest/Qiskit workflows | Time to specify, diagnose/fix a bug, mutation coverage, independent review |

For each round: select observed losses or unresolved obligations; profile,
form one testable hypothesis, implement an isolated change, rerun full
correctness and performance corpus, compare paired samples, adopt only
if improvement does not compromise mathematical guarantees, publish
negative results. Do not keep adding features or optimize against a
single synthetic corpus. No timing-based claim on inconclusive cases.
Memory/resource limits are separate from logical work budgets.

B1 near-Clifford uses T/Tdg as equivalent RZ rotations for pauli-prop;
global phase irrelevant to conjugation. Cap 2^T with T<=12, atol=0;
numerical cancellation and finite precision are not exact arithmetic.
Compare residual with a gray zone, record decisive coverage, assert
agreement when decisive and outside gray zone. The state baseline is
restricted to Clifford; non-Clifford expectation comparisons are B3.
Current B1 tests run on one shared CI image; no controlled hardware
claims. End-to-end speed baseline has already prepared contract input
representations for both sides. Additional user-facing contract creation
and diagnostic serialization measurements remain necessary.

## Release and adoption gaps

8-gate alphabet; 64-qubit native width ceiling and smaller limits in
other domains. T-count and support explosion, partial independent replay,
no arbitrary control flow/parameterized rotations/physical noise
model, no public registry or user-facing product maturity proof.
Need portable distributions, stable SDK-neutral representation,
documented errors, real examples, reproducible results and external
evaluation. Real user value is a saved debugging/verification task, not
merely a faster low-level operation.

B1 auxiliary branch does not change the #528 candidate or its pending
validation. No merge/release, no new speed results until CI artifacts.
