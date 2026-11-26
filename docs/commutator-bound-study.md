# Ordered product formula: commutator-bound study

Research-only. Refs #286, #287, #316, #254. No public API promotion.

For ordered Hermitian terms A_j, define B_j = sum of later terms. For time t
and r identical steps, the spectral-norm bounds used here are
- Lie: |t|^2/(2r) sum_j ||[A_j,B_j]||_2.
- symmetric Strang: |t|^3/r^2 sum_j (||[A_j,[A_j,B_j]]||_2/24
  + ||[B_j,[A_j,B_j]]||_2/12).
- Both may be capped at 2 because exact and approximate operators are unitary.

Reference: Childs et al., Theory of Trotter Error with Commutator Scaling,
Phys. Rev. X 11, 011020 (2021), https://doi.org/10.1103/PhysRevX.11.011020.
The single-step inequalities telescope because all factors are unitary.
These are mathematical error bounds for ideal, ordered, time-independent
Hermitian matrix products, not certified floating-point interval bounds,
device noise bounds, or guarantees for time-dependent Hamiltonians.

A local NumPy/SciPy-only reproduction ran 32 deterministic seeds (93200–93231),
2–3 wires, four unique Pauli labels, signed random time, two orders and
three step counts (1,4,16): 192 checks, zero violations with 2e-12 absolute
numerical slack. Maximum nonzero-bound error/bound ratios: 0.9987214843
(first order) and 0.9219664221 (second order). This is not a Ketary CI
result or a performance benchmark. The PR adds paired Ketary tests with an
independent matrix product and exponential; requires exact-head CI.
The floating-point slack is separate from the analytical approximation bound.
Dense cost grows exponentially; no runtime implementation or scaling claim.
