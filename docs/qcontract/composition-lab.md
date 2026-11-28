# Composition and contract ergonomics lab

A Plan checks conjunction on a single prepared snapshot. It does not
compose sequential contracts automatically. Design the final guarantee
before assembling components, then verify the combined source.

## Composition: local success does not establish the final behavior

Intent: preserve Z for every one-qubit input after two Hadamards.
Individual H components transform Z to X (and X to Z). The second
component must be selected to restore the intended overall action.
A misplaced Z between the two H gates reverses Z at the output,
even though the original components still satisfy their local tests.

```python
import json
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Pauli
from qcontract import Plan, invariant, pauli_on, prepare, transition

h = QuantumCircuit(1)
h.h(0)
local = Plan((transition("H maps Z to X", before="Z", after="X"),
              transition("H maps X to Z", before="X", after="Z")))
assert local.verify(prepare(h)).require().passed

final = Plan((invariant("Overall Z preserved", observable="Z"),))
# Same signed Pauli, different authoring ergonomics.
explicit = Plan((invariant("Overall Z preserved",
                            observable=pauli_on(1, ((0, "Z"),))),))
p = Pauli("Z").to_matrix()
cases = (("HH", ("h", "h"), "PASS"),
         ("HZH", ("h", "z", "h"), "FAIL"),
         ("HSH", ("h", "s", "h"), "FAIL"),
         ("HZZH", ("h", "z", "z", "h"), "PASS"))
rows = []
for name, gates, expected in cases:
    circuit = QuantumCircuit(1)
    for gate in gates:
        getattr(circuit, gate)(0)
    snapshot = prepare(circuit)
    result = final.verify(snapshot)
    alternate = explicit.verify(snapshot)
    a, b = result.results[0][1], alternate.results[0][1]
    u = Operator(circuit).data
    oracle = "PASS" if np.allclose(u.conj().T @ p @ u, p, rtol=0,
                                    atol=1e-12) else "FAIL"
    assert a.status == b.status == expected == oracle
    assert a.obligation == b.obligation and a.snapshots == b.snapshots
    assert result.explain() == alternate.explain()
    # These are logical work budgets, not elapsed-time guarantees.
    low = final.verify(snapshot, max_work=1)
    low_alt = explicit.verify(snapshot, max_work=1)
    assert low.explain() == low_alt.explain()
    assert not low.passed and low.results[0][1].status == "INCONCLUSIVE"
    rows.append({"case": name, "status": a.status,
                 "oracle": oracle, "full": result.explain(),
                 "bounded": low.explain()})
print(json.dumps({"cases": rows, "local_checks": 2,
                  "final_cases": len(rows), "alias_comparisons": 2*len(rows)},
                 allow_nan=False))
```

The local components are verified independently, not proofs about every
possible surrounding circuit. The numerical matrix oracle cross-checks
the small final examples; it does not replace exact verification.

## Developer review decision

1. Specify the overall requirement independently of the implementation.
2. Verify local component requirements for diagnosis where meaningful.
3. Verify the assembled circuit as a fresh snapshot.
4. If a local check succeeds and a final check fails, inspect composition
   and intervening operations. Do not weaken the final obligation.
5. Prefer explicit wire masks when they reduce indexing errors; equivalent
   authoring forms must retain obligation identity, status and budget behavior.

No automatic assume-guarantee proof, general sequential logic or new
mathematical predicate is introduced. Expected results are author-created
controls; verify them in isolated-wheel qualification before integration.
