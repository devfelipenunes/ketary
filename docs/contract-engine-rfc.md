# RFC — contract engine and native acceleration

Status: research proposal, not an approved runtime or packaging change.
Related #510 and #511. Preserve one public Python facade, Python 3.12,
Qiskit-authoritative circuit, existing Contract/Result behavior and limits.

## Architectural responsibilities

1. Python contract specification: immutable obligation, domain, quantifier,
   property, metric, tolerance, phase and method policy; snapshot vs operation
   vs channel vs statistical are distinct.
2. Analyzer: validate once, enforce scope and budgets before expensive calls,
   freeze one authoritative circuit export. Internal read-only packed
   instruction view is ephemeral, not another mutable IR.
3. Planner: pure capability/cost decision with deterministic explicit route,
   no silent guarantee weakening or optional-dependency fallback.
4. Backends: reuse NumPy/BLAS for dense linear algebra, Qiskit public Pauli
   and Clifford methods for symbolic invariants, existing optional QCEC for
   matching equivalence policies, statistical contracts for measured data.
   Add a private native kernel only after equivalent end-to-end advantage.
5. Composition: check domain compatibility, phases, error accumulation and
   contextual guarantees before deriving global obligations. Do not infer
   formal compositional proof from local numerical PASS.
6. Evidence: method/version, specification and input identity, exact scope,
   resource budget, residual, counterexample if available, reproducibility.
   No mutable-circuit cache, no hidden rerun, no implicit threads.

Native boundary: one batched call per obligation set, bounded packed buffer
or typed owned arrays, validate dtype/strides/length/overflow, no Python
callbacks during native loops. Release GIL only over owned/immutable data.
Native code has no authority to change circuit or verification semantics.
Errors/status distinguish invalid, unsupported, budget inconclusive, fail
and pass. For native wheel adoption propose Rust/PyO3 + maturin only after
ADR, measured benefit, license/SBOM and reproducible multi-platform wheels;
keep setuptools and public runtime unchanged during research. C++/pybind11
is a viable alternative. Use no fast-math where correctness is at risk.

## First experiment

Exact conjugation of one signed Hermitian Pauli by H,S,Sdg,X,Z,CX.
For up to 64 wires, two u64 masks and sign suffice; reverse gate traversal
computes U^dagger P U. O(g) word operations for this bounded representation,
O(g) packed input memory, not a general Clifford+T verifier. For one clean
ancilla and unitary U, U^dagger Z_a U=Z_a implies preservation of its zero
subspace; no implication of logical functionality. Non-equality requires
the property-specific witness/criterion before a full report can be issued.
Use independent dense Operator and Qiskit Pauli evolution oracles; compare
C++ and Rust C ABI, Python loop, public Qiskit with prebuilt Clifford and
full Ketary export. C ABI is a local research comparison, not PyO3 and not
production FFI. No public method or dependency added.

## Exit gates

E0 define semantics and report; E1 optimize existing admission/conversion
without changing guarantees; E2 benchmark native vs Qiskit and Python;
E3 specialize ancilla leakage including independent witnesses and tolerance
translation; E4 verify composition rules and adversarial cases; E5 integrate
internal engine only after review; E6 validate p50/p95, peak RSS, exact
head, compatibility, dedicated host #100, reproducible packaging and
external usability #165/#462. No timing assertions in shared CI. No
distribution or merge authorization inferred.

References: https://pyo3.rs/main/performance.html,
https://www.maturin.rs/project_layout.html,
https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.quantum_info.Pauli,
https://quantum-journal.org/papers/q-2026-07-23-2172/,
https://mqt.readthedocs.io/projects/qcec/en/stable/.

## Round 3 research increment

Prepared immutable ephemeral snapshot, gate classes validated once and wire indices mapped; no persistent cache or public API. Batch C++ bit-slicing up to 64 signed Paulis. Compare legacy export, preparation, scalar and batch, Qiskit Clifford prepared and full export with one tableau per batch. Exact sparse Clifford+T conjugation in Q(sqrt(2)), integer pairs over a shared power of two; no coefficient truncation. Caps: 64 wires, 100k gates, 32 T/Tdg, 4096 live terms and two million term visits; cap exhaustion is inconclusive, not failure or approximation. Numerical dense reference on small circuits. Leakage research: one arbitrary clean ancilla wire, 1–6 qubits, numeric unitary admission, SVD witness restricted to allowed inputs and direct reproduction, probability tolerance 1e-9 with diagnostic guard 1e-12; no certified roundoff. Generic effect residual squared agrees for exact unitary; timing routes differ in admission so no matched speedup claim. Includes analytic boundary case. No production changes or packaging.
