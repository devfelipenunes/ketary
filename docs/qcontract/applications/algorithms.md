# Algorithm suite — applications 12–25

Fourteen additional workloads, 103 fixed cases, no new runtime API.
The earlier portfolio is a separate application suite (#549/#550).
This branch does not depend on the pending #550 files.

| Workload | Requirement | Cases | Boundary |
|---|---|---:|---|
| Two-wire QFT | Fourier basis stabilizers and strict inverse roundtrip | 10 | Exact controlled-S decomposition only |
| Grid QPE | Recover each phase k/4 | 8 | Exact grid, known eigenstate |
| Grover search | Find each marked item in a four-item domain | 8 | One exact iteration |
| Deutsch–Jozsa | Distinguish constant and balanced affine functions | 8 | Two input wires; affine oracle family |
| Reversible half-adder | Preserve data; correct sum and carry | 8 | Basis contracts plus numeric clean-input isometry |
| Modular increment | Increment modulo eight | 16 | Basis contracts plus numeric full operator |
| Ideal random bits | Uniform joint computational-basis distribution | 6 | No entropy, randomness source or device certification |
| Five-qubit QEC | Finite single-error correctability and negative controls | 3 | No syndrome/recovery implementation |
| Period finding | Order-two instance for multiplication by 4 mod 15 | 4 | One-bit phase estimation; classical factor extraction |
| Coined quantum walk | One step on a four-cycle from position zero | 2 | No general multi-step walk |
| Phase kickback | Logical Z on arbitrary clean-input subspace | 2 | One known eigenstate |
| Syndrome extraction | One stabilizer parity for declared X errors | 4 | No dynamic measurement or correction |
| Conditional router | Fredkin truth table and selected invariants | 16 | Numeric operator cross-check, not exact full equivalence claim |
| Reversible comparator | One-bit unsigned greater-than flag | 8 | Basis-state guarantees |

Expected classifications are frozen before candidate output is inspected.
The QFT uses exact H, CX, T/Tdg gates; the largest dense numeric cross-check
uses five wires. Arithmetic uses an exact Clifford+T Toffoli decomposition.
The matrix or statevector checks are independent small numerical oracles,
not the engine's exact proof. A basis-state guarantee alone cannot prove
coherent phase correctness; the relevant examples explicitly distinguish
the additional numerical isometry/operator checks.

The period example uses a preselected order-two instance, not a general
Shor implementation or evidence of advantage. General QFT/QPE, VQE,
QAOA and signal processing with arbitrary rotations remain outside the
admitted exact gate domain. Do not add gates or relax contracts to claim
support. No hardware execution, user study or speed claim.

Run `python -I docs/qcontract/applications/run_algorithms.py` with the
matching qualified wheels. The JSON artifact records each result group.
All classifications and counts are expected until exact-head CI executes.
Record any genuine unresolved verdict, unsupported domain, incorrect
oracle or ergonomics issue separately; do not count it as a successful
application. Preserve previous suites in integrated qualification.
