# Tutorial: your first quantum circuit

Use Python 3.12.x and install the checkout with `python -m pip install -e '.[test]'`.
The examples here run against the installed package, not a second simulator.

## Prepare a Bell state and inspect it

```python
import ketary as q

circuit = q.Circuit(2).gates.h(0).gates.cx(0, 1)
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
circuit.gates.z(0)
after = circuit.run()
before.test.distribution(after).require()
assert before.test.state(after).status == "FAIL"
assert before.math.fidelity(after) < 1e-12
```

Identical measurement probabilities do not imply identical quantum states.
The relative phase changes the interference behavior. The earlier snapshot
does not change when the circuit changes.
