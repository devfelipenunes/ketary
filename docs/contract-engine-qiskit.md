# Qiskit comparison protocol (research)
Qiskit is the underlying authoritative circuit model, not an adversary.
Compare direct Qiskit APIs against the experimental Ketary verifier, with
same circuits, input observables, sign, witness requirements and timing
boundaries. Three independent jobs, pinned installed dependencies.
- Clifford: vectorized Qiskit Clifford/PauliList conjugation plus same
  Python exact witness and Report helpers, versus Rust batch reports.
  Preassigned circuit identity for Qiskit (no hashing cost); prepared
  vs existing native circuit and explicit Ketary export are distinct.
- Clifford+T: numerical Qiskit SparsePauliOp/Clifford block conjugation
  with exact-zero simplification tolerance, compare dense references and
  term coefficients; floating-point residual is NOT an exact certificate.
  Qiskit numeric route does not generate witnesses, replay Rust witness
  outside timing. Report timings separately, do not claim matched guarantee.
- Public snapshot: Qiskit Statevector expectation vs Ketary Contract on
  same zero-input GHZ, separate execution and predicate; report richness
  differs. Not universal verification.
Retain every raw sample and p50/p95. No noisy timing assertions, no
general SDK ranking or hardware claim. Shared CI only. No API changes.
