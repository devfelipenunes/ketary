# Native complex mathematical observables and channels

Candidate additions: explicit Result.math.expectation_complex for a bounded full-width native SparsePauliOp (not a new mutable operator model); Circuit.run_channel for a standard native Kraus CPTP map applied after ideal evolution. Independent tests use Kronecker Pauli matrices and explicit Kraus sums. No conversion to real, no implicit simulation, no mid-circuit noisy channel placement or physical execution. Limits in resource contracts. Qualification depends on exact-head CI.
