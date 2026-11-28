# Start here: your first contract-first program

QContract is an experimental exact contract layer for admitted ideal
Qiskit circuits. It does not replace Qiskit or guarantee physical execution.
Use CPython 3.12 and both local wheels from the same qualified commit.
Follow the [installation instructions](../qcontract-alpha-guide.md);
do not install an unrelated registry package with the same name.

## One requirement, one program, one verification

Before writing gates, require that the circuit maps Z to X on all
one-qubit inputs: U† X U = Z. Common global phase is allowed.
Predict that H satisfies the requirement and identity does not.

```python
from qiskit import QuantumCircuit
from qcontract import Plan, prepare, transition

plan = Plan((transition("Map Z to X", before="Z", after="X"),))
circuit = QuantumCircuit(1)
circuit.h(0)
verified = plan.verify(prepare(circuit)).require()
assert verified.passed
print(verified.explain())

# Challenge the same frozen requirement with an incorrect implementation.
wrong = plan.verify(prepare(QuantumCircuit(1)))
assert wrong.results[0][1].status == "FAIL"
assert not wrong.passed
# A resource limit is neither proof nor refutation.
bounded = plan.verify(prepare(circuit), max_work=1)
assert bounded.results[0][1].status == "INCONCLUSIVE"
```

A PASS proves this property in the admitted ideal domain, not arbitrary
program correctness. For a complete one-qubit H action up to phase,
also specify its independent X-to-Z transformation.

## What to do next

- Learn by doing: [tutorial](tutorial.md), [practice tasks](practice.md).
- Design a real requirement: [method v1 candidate](method-v1.md),
  [design canvas](contract-design.md), [pattern review](pattern-review.md).
- Look up syntax and scope: [reference](reference.md).
- Diagnose and integrate: [CI guide](how-to.md).
- Build a small algorithm/project: [practical guide](practical-guide.md),
  [modular project](project_example/verify.py).

The first block is executed during installed-wheel qualification.
A fresh source edit needs fresh verification; retain evidence and
reject required FAIL, INCONCLUSIVE and UNSUPPORTED.
