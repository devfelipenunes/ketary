# How-to guides

## Diagnose an aligned circuit

```python
import ketary as q

reference = q.bell().gates.x(0)
observed = q.bell().gates.z(0)
comparison = observed.debug.compare(reference)
assert comparison.step_index == 3
assert comparison.check.status == "FAIL"
```

Align equal-width, equal-length circuits at gate indices. This is a
zero-input trajectory comparison, not a root-cause proof.

## Construct a promised Deutsch-Jozsa oracle

```python
import ketary as q

c = q.deutsch_jozsa(q.parity_oracle("101"))
p = c.run().math.marginal_probabilities([2, 1, 0])
assert abs(p["101"] - 1) < 1e-12
```

The final wire is the target. Caller-supplied oracles must satisfy the
constant-or-balanced reversible bit-flip promise.

## Use native gates and verify transforms

```python
import ketary as q
from qiskit.circuit.library import RXGate

c = q.Circuit(2).append(RXGate(0.2), [0])
c.gates.x(1).gates.x(1)
optimized = c.optimize()
c.test.equivalent(optimized).require()
assert optimized.resources.summary().gate_count == 1
restored = q.Circuit.from_json(optimized.to_json())
restored.test.equivalent(optimized).require()
```

Use only supported standard gates with bound real angles. The returned
optimized and restored circuits are independent.
