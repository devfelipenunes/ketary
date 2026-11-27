# Why the contract language works

A signed Pauli is a Hermitian observable with eigenvalues ±1.
For an admitted unitary U, if U†BU=A then all states have the same
expectation of A before U and B after U. This is an operator identity,
not a general quantum Hoare triple. A zero-input eigencontract instead
requires expectation +1 on U|0>; for a Hermitian ±1 observable that
is equivalent to stabilization. A negative or zero expectation refutes
that property.

For Clifford circuits, U†PU is a signed Pauli. The expectation on |0>
is zero if an X component exists (including Y); otherwise it is the
sign. Batch tableau images are sufficient, avoiding full statevector
construction. The new candidate replays this calculation with an
independent ordered-Pauli evaluator. Non-Clifford propagation can grow
exponentially in T count and support. Exact dyadic Q(sqrt(2)) arithmetic,
cones, sparse expansions and decision diagrams can help, but budgets
may prevent a decision. Numeric MPS/statevector references are
cross-checks, not exact proofs.

Strict phase equivalence is stronger than global-phase equivalence.
A circuit global phase is irrelevant for isolated conjugation but can
matter under coherent control. Do not apply phase-insensitive results
to arbitrary controlled operations. Clean input and unnormalized
measurement-branch expectations likewise have different assumptions.

A QEC contract checks the finite error-set condition on the supplied
stabilizer code, not arbitrary noise or fault-tolerant hardware.
Snapshot and obligation hashes bind identity and reproducibility;
they are not cryptographic attestations of correctness. A full formal
verification of the Rust/Python implementation remains unproved.

Related work: QBricks (deductive circuit-building verification),
QbC (correctness by construction), quantum Hoare logic, Stim and QCEC.
QContract's candidate contribution is a pragmatic combination of exact
restricted predicates, accessible specifications, bounded verification
and evidence. Scientific novelty and external adoption need evaluation.
