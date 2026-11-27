# How to gate a quantum project in CI

Use an exact commit and both local wheels from the same qualification.
Verify SHA-256 and install both into a fresh CPython 3.12 environment.
Run pip check; do not share native binaries across platforms or commits.

```python
from qiskit import QuantumCircuit
from qcontract import Plan, transition, zero_input, prepare

def test_bell_contract():
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    plan = Plan((
        transition("Map Z", before="IZ", after="XX"),
        zero_input("X correlation", stabilizes="XX"),
        zero_input("Z correlation", stabilizes="ZZ"),
    ))
    plan.verify(prepare(circuit)).require()
```

Run with pytest in your project. require() accepts only all PASS.
Do not suppress INCONCLUSIVE or UNSUPPORTED to force a green pipeline.
When a check fails, inspect result.status, domain, witness, expectation,
route, obligation and snapshot IDs; replay supported results with the
same prepared circuit and contract. Replay can return None when it cannot
resolve within its budget or is unavailable. It is not a portable
proof certificate for every domain.

For a status-only screening batch, use prepared.statuses(*specs).
It preserves four statuses and the declared budget. Use full verify()
for diagnostics and replay. Do not treat a non-PASS status as a proof of
failure. Keep performance benchmarks out of unit-test thresholds on
shared runners; preserve all raw evidence and use controlled hardware
for performance acceptance.
