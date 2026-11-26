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

## Inspect a bounded basis table

```python
import ketary as q

r = q.bell().run()
text = r.math.table(["00", "11"])
assert "00 |" in text and "11 |" in text
print(text)
```

Default tables show the first 16 basis indices (not the most probable outcomes). Supply explicit labels for a targeted view. The table reports raw amplitudes and normalized probabilities, rounded for display only.


## Use explicit state and reduced density matrices

```python
import ketary as q
c = q.Circuit(2).h(0).cx(0, 1)
r = c.run(initial_state="00")
assert r.verify(expectations={"XX": 1, "ZZ": 1})["status"] == "PASS"
assert abs(r.math.purity([0]) - 0.5) < 1e-9
print(r.math.dirac())
```

## Fourier transform and search

```python
import ketary as q
c = q.qft(3)
c.compose(q.qft(3, inverse=True)).test.equivalent(q.Circuit(3)).require()
assert q.grover("101").run().math.probability("101") > 0.9
```


## Bind a reusable symbolic circuit

```python
import ketary as q
theta = q.Circuit.parameter("theta")
template = q.Circuit.symbolic(1).ry(theta, 0)
c = template.bind({theta: 3.141592653589793})
assert c.run().math.probability("1") > 0.999999
```

## Phase estimation

```python
import ketary as q
r = q.phase_estimation(3/8, 3).run()
assert r.math.marginal_probabilities([2, 1, 0])["011"] > 0.999999
```

## Optional local dynamic execution

Install `pip install -e '.[dynamic]'` in a Python 3.12 environment. Run
`q.teleportation(.37, -.63, verify=True).run_shots(shots=256, seed=42)`
after importing ketary as q. All output labels should start with 0 when
inverse preparation is enabled; the two Bell measurement bits are random.
This optional example is covered by the dynamic CI job, not the base docs suite.
