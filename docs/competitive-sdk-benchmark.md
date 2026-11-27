# COMP01 — Competitive SDK benchmark protocol

New research scope, separate from technical stabilization (#258), controlled
hardware (#100), independent evaluation (#165/#462) and paused Atlas (#460).
No public runtime dependencies, API, backend promotion or release.

## Phase A — common workload baseline

Four public routes: Ketary Circuit + owned Result state, Qiskit QuantumCircuit
+ Statevector copy, Cirq Circuit + complex128 Simulator, PennyLane
QuantumScript + default.qubit. These are not identical execution engines.
Device construction/import is outside prepared timing; end-to-end covers
circuit construction and owned state output, not import. Raw common logical
gate streams are authored independently of the SDKs; they are not idiomatic
algorithm implementations. Cirq can pack independent gates into moments.
Explicit wire ordering maps all outputs to little-endian complex128.
Seven families (GHZ, graph, QFT, variational, QAOA, Ising, random), three
widths (4, 8, 12), three seeds, three stages, 30 measurements and three warmups,
randomized route order per trial. Exact state oracle uses independent
bit-index equations, not Qiskit. Strict phase, normalization, max amplitude,
L2, fidelity and TV reported. Any mismatch fails the job before timing;
preserve failure logs, do not weaken tolerance or silently substitute routes.
Analytic Bell, basis/phase, QFT and negative controls guard the oracle.
Raw samples, p50/p95/p99, MAD and paired ratio recorded; no timing assertion.
Separate fresh Linux processes record pre-import, setup and post-execution
high-water RSS with three runs per route/width/seed; oracle after measurement.
RSS includes interpreter/libraries, not live payload, and increments are not
allocation counts. CPU affinity and single-thread env are recorded, not proof
of exclusive hardware or library-internal threading. Pin versions, retain
full resolved environment. Shared runner results are diagnostics.

## Remaining competitive programme (not implemented by phase A)

B. Idiomatic authored tasks: Bell/GHZ, QFT/QPE, Grover, BV, Simon, arithmetic,
   QAOA, VQE, quantum chemistry, QML and error correction. Measure source
   tokens/AST/explicit wires and gates, not adapter boilerplate; same output
   and accuracy. Independent usability remains #165/#462.
C. Symbolic differentiation, binding, sweeps, optimization; separate native
   gradients from parameter-shift and finite difference; equal budgets.
D. Dynamic circuits, measurement, noise and density: matched channels,
   shot budgets and confidence intervals, no unsupported-as-failure conflation.
E. Compilers: Qiskit, Cirq, pytket, Braket, BQSKit where applicable. Use pinned
   public Benchpress/QASMBench/MQT Bench inputs, common basis/connectivity and
   equivalent output, two-qubit count/depth and compile time separately.
F. Verification: strict operator, up-to-phase equivalence, selected-input,
   contract and witness checks are distinct guarantees. Include QCEC and
   intentionally injected faults, false PASS/FAIL/UNSUPPORTED, reproducible
   witnesses and scope. Do not time weaker proof against stronger proof.
G. Specialized engines: Aer, Lightning, qsim, QuEST, Qibo, CUDA-Q only on
   supported routes and hardware, separate setup/transfer, precision and
   native execution; no GPU claims from CPU. Dedicated host #100.
H. Final report: complete denominator, raw artifacts, effect sizes, paired
   confidence intervals across independent runs, negative results and
   Pareto frontiers by task; no arbitrary single composite winner.

References:
- Benchpress: https://doi.org/10.1038/s43588-025-00792-y
- QASMBench: https://doi.org/10.1145/3550488
- MQT Bench: https://mqt.readthedocs.io/projects/bench/en/stable/
- PennyLane execute: https://docs.pennylane.ai/en/stable/code/api/pennylane.execute.html

Acceptance: exact candidate semantic and CI checks, raw artifacts inspected,
report limitations and mismatches. A queued workflow is not evidence.
