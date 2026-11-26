# Tutorial: your first quantum circuit

Use Python 3.12.x and install the checkout with `python -m pip install -e '.[test]'`.
The examples here run against the installed package, not a second simulator.

## Prepare a Bell state and inspect it

```python
import ketary as q

circuit = q.Circuit(2).h(0).cx(0, 1)
result = circuit.run()
result.test.normalized().require()
result.test.probability("00", 0.5).require()
result.test.probability("11", 0.5).require()
assert sum(result.sample(shots=100, seed=42).values()) == 100
print(circuit.visualize.text())
```

H creates superposition on wire zero. CX correlates the two wires.
The ideal outcomes are 00 and 11, each with probability one half.
Sampling is terminal and does not collapse or mutate the Result snapshot.

## Observe interference and relative phase

```python
import ketary as q

circuit = q.bell()
before = circuit.run()
circuit.z(0)
after = circuit.run()
before.test.distribution(after).require()
assert before.test.state(after).status == "FAIL"
assert before.math.fidelity(after) < 1e-12
```

Identical measurement probabilities do not imply identical quantum states.
The relative phase changes the interference behavior. The earlier snapshot
does not change when the circuit changes.


## Reuse a parameterized circuit

```python
import ketary as q
theta = q.Circuit.parameter("theta")
template = q.Circuit.symbolic(2).ry(theta, 0).cx(0, 1)
plan = template.sweep(theta=[0, 0.5, 1])
results = plan.run()
for angle, result in zip([0, 0.5, 1], results, strict=True):
    result.test.normalized().require()
    print(angle, result.math.expectation(q.Z(0) @ q.Z(1)))
```

Sweeps are zipped rather than Cartesian, and all admitted rows bind before
execution. Up to 32 results are retained; use a smaller batch when working
with wide states. The plan does not simulate until run is called.

## Verify a reusable mathematical contract and replay a circuit

```python
import ketary as q
expected = q.bell()
observed = expected.copy().z(0)
contract = expected.contract(expectations={q.X(0) @ q.X(1): 1})
contract.verify(expected.run()).require()
assert contract.verify(observed.run()).status == "FAIL"
restored = q.Circuit.from_json(expected.to_json())
restored.test.equivalent(expected).require()
```

An expectation check covers the selected predicate on one ideal state; it
is not a proof of full operator equivalence. Replay uses a bounded logical
schema, not executable object deserialization.

## Inspect cost before executing

```python
import ketary as q
circuit = q.Circuit(4).apply(q.bell(), wires=[3, 1])
page = circuit.inspect(start=0, limit=1)
assert len(page["operations"]) == 1
assert circuit.resources.summary().gate_count == 2
result = circuit.run()
assert abs(sum(result.math.marginal_probabilities([3, 1]).values()) - 1) < 1e-9
print(result.math.top_probabilities(k=2))
```

Inspection and resource reports are logical, not hardware estimates. A dense
complex128 state stores 16 * 2**n bytes before scratch, copies and retained
results. Use targeted queries instead of exporting all probabilities.
Research-only chunking and buffer alternatives are not enabled merely by
using these APIs. See [resource contracts](resource-contracts.md) and
[verification scope](verification-guide.md).

## Learning path

1. Build and run a small circuit; learn wire order and snapshot ownership.
2. Reuse symbolic blocks; bind and sweep explicitly.
3. Express observables and reusable contracts; distinguish state and operator checks.
4. Inspect, diagnose and reproduce a deliberately introduced defect.
5. Study Hamiltonian evolution, reversible composition and variational workflows.
6. Compare matched native outputs and costs using the research profiles.

The examples are authored qualification exercises, not independent human
usability results. Use the [language guide](language-guide.md),
[mathematical guide](mathematical-guide.md) and [how-to guides](how-to.md)
for the next stages.
