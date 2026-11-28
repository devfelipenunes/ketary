# Practice: specify, diagnose and repair

Each task uses only the admitted ideal circuit domain. Write down the
expected property and defect before running the code. These worked
examples are practice tasks, not evidence of independent user adoption.

## Task 1 — Diagnose an incorrect inverse

Requirement: the complete circuit is the identity on arbitrary input,
not simply a circuit that returns the zero state to zero.

```python
from qiskit import QuantumCircuit
from qcontract import Plan, transition, zero_input, prepare, Named

bad = QuantumCircuit(1)
bad.s(0)
bad.s(0)
identity = prepare(QuantumCircuit(1))
p = prepare(bad)
plan = Plan((
    zero_input("Zero remains zero", stabilizes="Z"),
    transition("Preserve X on every input", before="X", after="X"),
    Named("Strict identity", p.equivalent_to(identity, strict=True)),
))
result = plan.verify(p)
assert [r.status for _, r in result.results] == ["PASS", "FAIL", "FAIL"]
assert not result.passed
assert result.explain()[1]["status"] == "FAIL"
assert p.replay(plan.obligations[1].specification, result.results[1][1]) is True

fixed = QuantumCircuit(1)
fixed.s(0)
fixed.sdg(0)
q = prepare(fixed)
fixed_plan = Plan(plan.obligations[:2] + (
    Named("Strict identity", q.equivalent_to(identity, strict=True)),
))
assert fixed_plan.verify(q).require().passed
```

The first property admits both circuits; the operator property detects
the sign reversal. Strict identity expresses the complete intended
unitary for this one-wire task. Replay confirms a supported report,
not every property in the plan.

## Task 2 — Distinguish a proof from a resource limit

```python
h = QuantumCircuit(1)
h.h(0)
engine = prepare(h)
property_h = transition("H maps Z to X", before="Z", after="X")
small = Plan((property_h,)).verify(engine, max_work=1)
assert small.results[0][1].status == "INCONCLUSIVE"
assert not small.passed
try:
    small.require()
except AssertionError:
    pass
else:
    raise AssertionError("Unresolved proof must not pass")
full = Plan((property_h,)).verify(engine)
assert full.require().passed
assert full.results[0][1].obligation == small.results[0][1].obligation
assert full.results[0][1].snapshots == small.results[0][1].snapshots
```

A larger logical budget here resolves the same obligation. This does
not imply that increasing resources always yields a proof, nor that
the work budget bounds elapsed time.

## Task 3 — Keep wire indices explicit

```python
from qcontract import Contract, StateEigen, Pauli, pauli_on

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)
engine = prepare(bell)
before = pauli_on(2, ((0, "Z"),))
after = pauli_on(2, ((0, "X"), (1, "X")))
assert before == Pauli("IZ") and after == Pauli("XX")
spec = Plan((
    Named("Map logical observable", Contract(requires=before, ensures=after)),
    Named("Positive X correlation", StateEigen(after)),
))
assert spec.verify(engine).require().passed
try:
    pauli_on(2, ((0, "Z"), (0, "X")))
except ValueError:
    pass
else:
    raise AssertionError("Duplicate wire must be rejected")
```

Masks do not retain declared width; query admission checks their
actual bits against the prepared circuit. Explicit wire indexing
avoids reversing a multiwire string accidentally.

## Evidence to record

For a practice task, retain the independent expected statuses,
observed statuses, snapshot/obligation IDs, requested logical budget
and reported domain. Distinguish a programming input error (exception)
from a mathematical FAIL, an unresolved INCONCLUSIVE, and an
UNSUPPORTED domain. Use a fresh snapshot after circuit edits.
