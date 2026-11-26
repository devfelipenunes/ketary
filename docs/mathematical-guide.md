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
