# Scope review lab — observable rewrite

This lab extends the state-preparation and clean-workspace examples with
an all-input observable transformation. It is an author-created teaching
case, not an external developer study.

## Design before gates

Intent: implement Hadamard's action on both X and Z. Scope: all single
qubit inputs. Wire 0 is logical. A gate-sequence rewrite is allowed,
and the two-observable requirement is insensitive to a common global
phase. Strict equality to H is a separate, optional stronger requirement.
No source global-phase annotation is needed or admitted in this example.

A single transition Z -> X can be satisfied by H followed by X, which
violates the other intended transition X -> Z. Conversely H followed
by Z satisfies the latter but violates the former. Identity satisfies
neither. The alternative H,H,H satisfies both and strict equivalence.
Predictions follow from Pauli conjugation, independently of the verifier.

```python
import json
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Pauli
from qcontract import Named, Plan, pauli_on, prepare, transition

x = pauli_on(1, ((0, "X"),))
z = pauli_on(1, ((0, "Z"),))
intent = Plan((
    transition("Map Z to X", before=z, after=x),
    transition("Map X to Z", before=x, after=z),
))
reference = QuantumCircuit(1)
reference.h(0)
ref = prepare(reference)
h = Operator(reference).data
px, pz = Pauli("X").to_matrix(), Pauli("Z").to_matrix()
cases = (
    ("H", ("h",), "positive", ("PASS", "PASS", "PASS")),
    ("HHH", ("h", "h", "h"), "allowed", ("PASS", "PASS", "PASS")),
    ("H then X", ("h", "x"), "defect", ("PASS", "FAIL", "FAIL")),
    ("H then Z", ("h", "z"), "defect", ("FAIL", "PASS", "FAIL")),
    ("identity", (), "defect", ("FAIL", "FAIL", "FAIL")),
)
rows = []
for name, gates, kind, expected in cases:
    circuit = QuantumCircuit(1)
    for gate in gates:
        getattr(circuit, gate)(0)
    prepared = prepare(circuit)
    # Bind the independent reference to the current snapshot; strict
    # equality is reported separately, not used to decide the intent.
    plan = Plan(intent.obligations + (
        Named("Optional strict equality", prepared.equivalent_to(ref, strict=True)),
    ))
    outcome = plan.verify(prepared)
    observed = tuple(result.status for _, result in outcome.results)
    u = Operator(circuit).data
    oracle = tuple("PASS" if np.allclose(a, b, rtol=0, atol=1e-12) else "FAIL"
                   for a, b in ((u.conj().T @ px @ u, pz),
                                (u.conj().T @ pz @ u, px), (u, h)))
    assert observed == expected == oracle, (name, observed, expected, oracle)
    accepted = all(s == "PASS" for s in observed[:2])
    assert accepted == (kind != "defect")
    rows.append({"case": name, "classification": kind, "expected": expected,
                 "observed": observed, "oracle": oracle,
                 "reports": outcome.explain()})

# Obligation ablation: each single transition misses a distinct true
# defect. The strict diagnostic is deliberately excluded from scoring.
defects = [row for row in rows if row["classification"] == "defect"]
allowed = [row for row in rows if row["classification"] == "allowed"]
detected = sum("FAIL" in row["observed"][:2] for row in defects)
accepted = sum(all(s == "PASS" for s in row["observed"][:2]) for row in allowed)
assert (detected, len(defects), accepted, len(allowed)) == (3, 3, 1, 1)
ablated = [sum(row["observed"][i] == "FAIL" for row in defects) for i in (0, 1)]
assert ablated == [2, 2]
unresolved = intent.verify(ref, max_work=1)
assert not unresolved.passed
assert all(r.status == "INCONCLUSIVE" for _, r in unresolved.results)
print(json.dumps({"cases": rows, "checks": 3 * len(rows),
                  "defects_detected": detected, "defects_total": len(defects),
                  "allowed_accepted": accepted, "allowed_total": len(allowed),
                  "single_obligation_detected": ablated,
                  "budget_control": unresolved.explain()}, allow_nan=False))
```

Expected: 15 decided status comparisons and two unresolved budget
controls; 3/3 seeded defects detected by the two intended obligations,
1/1 allowed rewrite accepted; each single obligation detects only 2/3
defects. These are expected results until installed-wheel CI executes
the block. The numeric oracle is a small independent cross-check, not
the engine's exact proof.

## Recursive design decision

Do not strengthen the specification simply to make every different
circuit fail. Add the missing X -> Z obligation because it was part of
the stated intent. Keep strict equality optional unless exact phase
is required. A surviving permitted rewrite is a successful control.
Store the original requirement, source snapshot and per-obligation
reports; distinguish decided cases from the budget control.

Next: [contract design](contract-design.md), [quality controls](testing.md)
and [ten-cycle roadmap](ten-cycle-roadmap.md).
