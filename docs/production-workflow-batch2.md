# Production program corpus — second application batch

27 authored executable programs spanning promise problems, hidden parity and
period, marked-set amplification, eigenphase estimation, coherent coding,
dynamic teleportation, overlap and complex matrix-element tests, reversible
arithmetic and comparator, linear reversible logic, exact Clifford+T synthesis,
entanglement swapping, phase-error recovery, error-detecting code, tomography,
state discrimination, ideal BB84 basis sifting, discrete quantum walk, fermionic
algebra and transport, two-site Hubbard dynamics, Fisher-information scaling,
rank-deficient natural gradient, geometric phase and a depolarizing channel.

The test file contains independent truth-table, analytic or dense matrix
oracles. The teleportation program requires the optional local Aer extra;
report Core skips and Dynamic results separately. The BB84 task is ideal basis
sifting only, not a cryptographic security claim; no physical hardware or
independent participants. Count 27 fixtures in this batch, not 27 automatically
new global tasks. The 100-distinct-program ledger requires semantic deduplication
against earlier 37-task corpus, recovery routes, previous 12 programs and
existing examples. Never count randomized seeds or prompt-only tasks as
additional program intents.

## Strict synthesis regression candidate

Prior default native synthesis failed the four-wire Hubbard operator at residual
8.892498603556574e-6 (phase-aligned residual unchanged). Candidate fallback is
restricted to one 3–5-wire HamiltonianGate and one zero-ancilla native Isometry
synthesis (https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.Isometry).
It corrects global phase explicitly, then independently rechecks the complete
operator at the existing 1e-9 component tolerance, canonical gate basis and
10,000-output-instruction cap. No new public API, approximation contract or
backend. Negative test replaces both native transpile calls with a wrong result
and checks builder atomicity. Three Hubbard parameter cases use a dense SciPy
oracle; they are one application intent, not three. Candidate only until CI.
