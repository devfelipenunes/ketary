# Mathematical qualification: time derivatives, tensor blocks, preparation

Refs #284 #281 #288. Tests-only extension, no runtime/API change.
36 signed-time cases: commuting Z/ZZ/identity Hamiltonian, strict full
native and independent expm operator, complex-input state derivative
against -iH psi via a central-difference diagnostic (1e-8 absolute),
and observable derivative against i<[H,O]> via exact supported
occurrence-shift Jacobian (1e-9 absolute). Identity phase is retained in
state derivatives and cancels in expectations. Negative noncommuting
preflight. No arbitrary Hamiltonian differentiation or new API.

12 disjoint tensor cases: every three-wire permutation, phased single
and entangled two-wire blocks, independent permuted Kronecker matrix,
Qiskit composition, arbitrary input, source immutability and invalid
mapping rollback. This is not implicit tensor notation or automatic
ancilla allocation.

15 complex amplitude cases at widths 1..5 plus product and negative
controls. Compare complete native StatePreparation extension, including
phase, arbitrary input, inverse and unitarity. A state vector specifies
only one column, so the other columns are Qiskit's pinned extension, not
a unique independent mathematical unitary. No reset or implicit
normalization. Existing synthesis and resource limits are unchanged.
