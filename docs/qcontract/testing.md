# Test the quality of your contracts

A passing property is not automatically a correct implementation.
Use the following review process before accepting a Plan:

1. Write the intended input scope and expected guarantee independently
   of the implementation.
2. Establish a known-good circuit.
3. Select meaningful defects and equivalent or allowed variations.
4. Predict a status vector before verification. Compare with a small
   independent reference when practical.
5. If a wrong implementation survives, decide whether it violates the
   stated scope. Strengthen the specification only when the missing
   requirement is actually intended.
6. Keep positive, negative, equivalent and unresolved controls in CI.

## State preparation: detect missing gates, phase and bit errors

For GHZ+, three independent stabilizers XXX, IZZ and ZZI determine
a one-dimensional joint +1 eigenspace. Individual Z correlations
cannot distinguish GHZ+ from GHZ-. These named cases have independently
predicted status vectors. The statevector check is a numerical
cross-check for this three-wire example, not the engine's proof.

```python
import json
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli as QiskitPauli
from qcontract import Plan, zero_input, prepare

labels = ("XXX", "IZZ", "ZZI")
plan = Plan(tuple(zero_input(label, stabilizes=label) for label in labels))

def ghz(*, initial_h=True, last_cx=True, suffix=()):
    circuit = QuantumCircuit(3)
    if initial_h:
        circuit.h(0)
    circuit.cx(0, 1)
    if last_cx:
        circuit.cx(1, 2)
    for gate, wire in suffix:
        getattr(circuit, gate)(wire)
    return circuit

state_cases = (
    ("original", ghz(), ("PASS", "PASS", "PASS")),
    ("missing H", ghz(initial_h=False), ("FAIL", "PASS", "PASS")),
    ("missing final CX", ghz(last_cx=False), ("FAIL", "PASS", "FAIL")),
    ("phase flip", ghz(suffix=(("z", 0),)), ("FAIL", "PASS", "PASS")),
    ("bit flip 0", ghz(suffix=(("x", 0),)), ("PASS", "FAIL", "PASS")),
    ("bit flip 1", ghz(suffix=(("x", 1),)), ("PASS", "FAIL", "FAIL")),
    ("bit flip 2", ghz(suffix=(("x", 2),)), ("PASS", "PASS", "FAIL")),
    ("two phase flips", ghz(suffix=(("z", 0), ("z", 2))), ("PASS", "PASS", "PASS")),
    ("identity pair", ghz(suffix=(("h", 1), ("h", 1))), ("PASS", "PASS", "PASS")),
)
state_rows = []
for name, circuit, expected in state_cases:
    outcome = plan.verify(prepare(circuit))
    observed = tuple(result.status for _, result in outcome.results)
    vector = Statevector.from_instruction(circuit)
    oracle = tuple(
        "PASS" if np.isclose(vector.expectation_value(QiskitPauli(label)),
                             1, rtol=0, atol=1e-12) else "FAIL"
        for label in labels
    )
    assert observed == expected == oracle, (name, observed, expected, oracle)
    state_rows.append({"case": name, "statuses": observed})
assert not plan.verify(prepare(ghz()), max_work=1).passed
assert all(r.status == "INCONCLUSIVE"
           for _, r in plan.verify(prepare(ghz()), max_work=1).results)
print(json.dumps({"state_cases": state_rows}))
```

The phase-flip, missing-H and bit-flip cases reveal different
specification weaknesses. Two phase flips are permitted by the state
specification; they need not be equivalent as all-input operators.
Do not count equivalent controls as undetected defects.

## Clean workspace: distinguish an allowed action from a missing requirement

The workspace is wire 1 and the logical input is wire 0. The initial
plan asks for clean ancillas and preservation of logical Z, not a
specific logical unitary. A logical Z gate can pass both. If the actual
requirement is the identity on the whole register, add strict
equivalence to an independent reference. That is a stronger, different
scope, not a replacement for clean-input contracts in general.

```python
from qiskit.quantum_info import Operator
from qcontract import clean_ancillas, invariant, Named

workspace = Plan((
    clean_ancillas("Restore wire 1", wires=(1,)),
    invariant("Preserve logical Z", observable="IZ"),
))
identity = QuantumCircuit(2)
ref = prepare(identity)
logical_z = QiskitPauli("IZ").to_matrix()

def cleanup(*, uncompute=True, suffix=()):
    circuit = QuantumCircuit(2)
    circuit.cx(0, 1)
    if uncompute:
        circuit.cx(0, 1)
    for gate, wire in suffix:
        getattr(circuit, gate)(wire)
    return circuit

workspace_cases = (
    ("original", cleanup(), ("PASS", "PASS", "PASS")),
    ("missing uncompute", cleanup(uncompute=False), ("FAIL", "PASS", "FAIL")),
    ("workspace X", cleanup(suffix=(("x", 1),)), ("FAIL", "PASS", "FAIL")),
    ("logical X", cleanup(suffix=(("x", 0),)), ("PASS", "FAIL", "FAIL")),
    ("logical Z", cleanup(suffix=(("z", 0),)), ("PASS", "PASS", "FAIL")),
    ("logical H", cleanup(suffix=(("h", 0),)), ("PASS", "FAIL", "FAIL")),
    ("workspace Z", cleanup(suffix=(("z", 1),)), ("PASS", "PASS", "FAIL")),
    ("identity pair", cleanup(suffix=(("x", 0), ("x", 0))), ("PASS", "PASS", "PASS")),
)
workspace_rows = []
for name, circuit, expected in workspace_cases:
    engine = prepare(circuit)
    stronger = Plan(workspace.obligations + (
        Named("Strict whole-register identity", engine.equivalent_to(ref, strict=True)),
    ))
    observed = tuple(r.status for _, r in stronger.verify(engine).results)
    u = Operator(circuit).data
    # Columns 0,1 represent arbitrary logical inputs with wire 1 clean.
    # Rows 2,3 are leakage into nonzero workspace states.
    clean = np.allclose(u[2:, :2], 0, rtol=0, atol=1e-12)
    preserves = np.allclose(u.conj().T @ logical_z @ u, logical_z,
                            rtol=0, atol=1e-12)
    identical = np.allclose(u, np.eye(4), rtol=0, atol=1e-12)
    oracle = tuple("PASS" if value else "FAIL"
                   for value in (clean, preserves, identical))
    assert observed == expected == oracle, (name, observed, expected, oracle)
    workspace_rows.append({"case": name, "statuses": observed})
print(json.dumps({"workspace_cases": workspace_rows}))
```

These 17 circuit cases and 51 status comparisons are a small,
developer-authored teaching matrix. They measure neither general
mutation coverage nor external user productivity. In a real project,
choose defects based on the actual mathematical requirement, keep
scope-specific expected results, and do not count equivalent variants
as failures of the specification.
