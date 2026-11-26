# Mathematical conventions

Ketary uses Qiskit's little-endian wire numbering: in a full label q[n-1]
is the leftmost character, q[0] is the rightmost. Ordered subsystem queries
instead follow the supplied wire order. All angles are radians.

A pure snapshot stores a complex vector of dimension 2**n. Born probabilities
use squared amplitude magnitudes divided by the stored squared norm.
`math.statevector()` returns a defensive copy. Fidelity of pure states is the
squared magnitude of their normalized inner product. It ignores global phase;
raw state residuals can preserve phase. Neither proves operator equivalence.

```python
import ketary as q
r = q.bell().run()
assert abs(r.math.probability("00") - 0.5) < 1e-9
assert abs(r.math.expectation("XX") - 1) < 1e-9
assert abs(r.math.purity([0]) - 0.5) < 1e-9
assert r.math.purity() == 1
print(r.math.density_matrix([0]))
```

A reduced density matrix is the partial trace over the unselected wires.
The Schmidt values are singular values across a selected/rest partition;
entropy uses base-two logarithms. A Pauli string is a tensor product of
Hermitian I/X/Y/Z operators. Weighted real sums define Hermitian observables.
The variance is the squared norm of (A - expectation(A)) applied to a
normalized state. Dense and streamed methods have different cost guards.

A statevector Result describes ideal pure evolution. Its terminal samples
are not intermediate measurements. A ShotResult records empirical counts
from the optional local dynamic mode; sampling variation must be handled
statistically. See [verification guide](verification-guide.md).


## Formula contracts and independent reference oracles

For a normalized pure state psi, a real Pauli sum H, and a unitary U:

- Born rule: p(x) = |psi[x]|^2, sum_x p(x) = 1.
- Expectation: E(H) = psi^dagger H psi; real for Hermitian H.
- Variance: Var(H) = ||(H - E(H) I) psi||^2; nonnegative.
- Reduced state: rho_A[a,b] = sum_e psi[a,e] conjugate(psi[b,e]).
  The first supplied subsystem wire is the most significant output axis.
- Purity: Tr(rho_A^2); Schmidt coefficients squared are eigenvalues
  of rho_A; entropy = -sum_i lambda_i log2(lambda_i), with 0 log2 0 = 0.
- Exact commuting evolution: U(t) = exp(-i t H), with identity terms
  contributing global phase. Noncommuting sums are not silently approximated.
- Expectation Jacobian for supported one-angle gates: for parameter x,
  dE/dx = sum_j (d theta_j/dx) [E(theta_j+pi/2)-E(theta_j-pi/2)]/2,
  shifting only occurrence j; other angles fixed. Global phase contributes
  zero to expectation derivatives. This is not a statevector derivative.
- Strict operator equality is distinct from equality up to global phase,
  state fidelity, matching probabilities and selected predicate agreement.

Independent dense oracles and analytic derivatives are tested in
tests/test_production_math_oracles.py. Numerical tolerances are absolute
for the fixtures; they are not a universal forward-error bound. See
[production qualification](production-qualification.md) for evidence gates.

Controlled rotations have generator eigenvalues 0, +1/2, -1/2. Their expectation derivative uses 1/2 times the difference at theta +/- pi/2 plus (1-sqrt(2))/4 times the difference at theta +/- pi. The two nonzero frequency gaps 1/2 and 1 satisfy this identity exactly in the ideal model; chain rule sums occurrences. No finite-difference approximation for these gates.

For duplicate Pauli labels and bounded pairwise products, finite rounded real and imaginary contributions are aggregated using compensated fsum independently. No numerical truncation or Hermitian tolerance is applied to imported imaginary residuals. This reduces cancellation error, but is not arbitrary precision: individual products still round and overflow is explicitly rejected.
