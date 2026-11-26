# How-to guides

## Diagnose an aligned circuit

```python
import ketary as q

reference = q.bell().x(0)
observed = q.bell().z(0)
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
c.x(1).x(1)
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
r.verify(expectations={q.X(0) @ q.X(1): 1, "ZZ": 1}).require()
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
c = template.bind(theta=3.141592653589793)
assert c.run().math.probability("1") > 0.999999
```

## Phase estimation

```python
import ketary as q
r = q.phase_estimation(3/8, 3).run()
assert q.decode_phase_estimation(r, precision=3).phase == 3/8
```

## Optional local dynamic execution

Install `pip install -e '.[dynamic]'` in a Python 3.12 environment. Run
`q.teleportation(.37, -.63, verify=True).run_shots(shots=256, seed=42)`
after importing ketary as q. All output labels should start with 0 when
inverse preparation is enabled; the two Bell measurement bits are random.
This optional example is covered by the dynamic CI job, not the base docs suite.


## Recover a Bernstein–Vazirani secret

```python
import ketary as q

secret = "1011"
c = q.Circuit(5).x(4).h(range(5))
c.apply(q.parity_oracle(secret), wires=range(5)).h(range(4))
report = q.decode_bernstein_vazirani(c.run())
assert report["status"] == "PASS" and report["label"] == secret
```

The target is the highest wire; the secret uses highest-wire-first labels.
This is a promised parity oracle, not arbitrary classical function synthesis.

## Recover a Simon period from ideal support

```python
import ketary as q

secret = "101"
r = q.simon(secret).run()
p = r.math.marginal_probabilities([2, 1, 0])
support = [label for label, value in p.items() if value > 1e-12]
assert q.recover_simon(support, 3) == secret
```

Ideal support is not sampled hardware evidence. For a shot-based workflow,
record counts, seed and the possibility of insufficient independent rows.

## GHZ parity and a bounded QAOA objective

```python
import ketary as q
from math import pi

ghz = q.Circuit(3).h(0).cx(0, 1).cx(0, 2)
ghz.run().test.expectation(q.X(0) @ q.X(1) @ q.X(2), 1).require()

# One-layer two-vertex MaxCut. Cost = (I - Z0 Z1) / 2.
gamma, beta = pi/2, pi/8
cost = .5*q.I() - .5*(q.Z(0) @ q.Z(1))
trial = q.Circuit(2).h([0, 1]).evolve(cost, time=gamma)
trial.rx(2*beta, [0, 1])
assert abs(trial.run().math.expectation(cost) - 1) < 1e-9
```

These are authored, bounded examples, not an optimizer or performance
guarantee for larger graphs. The cost phase is retained by evolve; all
simulations are explicit. Use selected observables and existing resource
limits rather than allocating full distributions for wide circuits.
