# Tutorial: your first exact quantum contracts

Install the two local wheels from the same qualified commit in a clean
CPython 3.12 environment (see [installation guide](../qcontract-alpha-guide.md)).
Do not install an unrelated package with the same name from a registry.
The 0.1.0a3 candidate is integrated. These exact Python blocks are
executed during isolated-wheel qualification by check_examples.py.

## 1. Predict a transformation

Before running this, predict what H does to Z and X. Specify the property,
implement the circuit, then verify it.

```python
from qiskit import QuantumCircuit
from qcontract import Plan, transition, prepare

spec = Plan((transition("H maps Z to X", before="Z", after="X"),))
circuit = QuantumCircuit(1)
circuit.h(0)
outcome = spec.verify(prepare(circuit))
assert outcome.require().passed
print(outcome.explain())
wrong = QuantumCircuit(1)
wrong.x(0)
assert spec.verify(prepare(wrong)).results[0][1].status == "FAIL"
```

Expect PASS. Change H to X and predict why the same property fails.

## 2. Learn about state and operator scope

```python
from qcontract import invariant, zero_input

identity = prepare(QuantumCircuit(1))
plan = Plan((
    invariant("Identity preserves X", observable="X"),
    zero_input("Zero state stabilizes X", stabilizes="X"),
))
outcome = plan.verify(identity)
assert [result.status for _, result in outcome.results] == ["PASS", "FAIL"]
print([(name, result.status) for name, result in outcome.results])
```

Expect PASS then FAIL. The first is about every input, the second about
the state |0>. They are not interchangeable.

## 3. Bell states: predict, verify, modify

```python
spec = Plan((
    transition("Transform Z", before="IZ", after="XX"),
    zero_input("Bell X correlation", stabilizes="XX"),
    zero_input("Bell Z correlation", stabilizes="ZZ"),
))
bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
assert spec.verify(prepare(bell)).passed
bell.z(0)
mutated = spec.verify(prepare(bell))
assert [result.status for _, result in mutated.results] == ["FAIL", "FAIL", "PASS"]
print(mutated.explain())
```

Expect FAIL, FAIL, PASS after the mutation. Explain why a phase flip
changes the X correlation but not the Z correlation. Qiskit labels are
highest wire first. Use pauli_on(2, ((0, "Z"),)) for wire zero.

## 4. Learn ancilla cleanup by uncomputation

```python
from qcontract import clean_ancillas

c = QuantumCircuit(2)
c.cx(0, 1)
c.cx(0, 1)
spec = Plan((clean_ancillas("Return workspace", wires=(1,)),))
spec.verify(prepare(c)).require()
c.cx(0, 1)
assert not spec.verify(prepare(c)).passed
```

A single CNOT can correlate the initially clean target with the control;
it is not a general quantum copying operation.
The guarantee is for all logical inputs with the ancilla initially zero,
not only an all-zero example.

## 5. Explore the remaining families

Use [reference](reference.md) and [explanation](explanation.md) to study
strict vs phase-insensitive equivalence, separability, rational sums,
finite Pauli mixtures, measurement branches and finite QEC. Their
executable small examples live in contract_first_tests.py. These are
separate mathematical domains, not general-purpose quantum assertions.

## 6. Budget and status

Set max_work=1 for the three-obligation Bell plan: expect INCONCLUSIVE,
not FAIL. A strict require() rejects unresolved results. Read the
explanation and inspect the scope before increasing resources. Do not
interpret a PASS on one property as verification of the entire program.

## 7. Execute only after the specification is established

Run the verified ideal source circuit using your chosen Qiskit backend.
A source edit requires a fresh prepare() and verification. Transpilation
may change representation, and hardware has noise; this tutorial does
not assert equivalence of arbitrary transpiled circuits or error-free
hardware execution.
