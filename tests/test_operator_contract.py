"""Full-operator regressions for the supported experimental subset.

These compare more than the |0...0> output and deliberately preserve phase.
"""
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import ketary as q


@pytest.mark.parametrize("seed", [7, 42, 2026, 20261125])
def test_seeded_roundtrip_operator(seed):
    rng = np.random.default_rng(seed)
    raw = QuantumCircuit(3, global_phase=float(rng.uniform(-np.pi, np.pi)))
    for _ in range(32):
        gate = rng.choice(["h", "x", "z", "cx", "swap"])
        wires = rng.choice(3, size=2 if gate in ("cx", "swap") else 1, replace=False)
        getattr(raw, gate)(*(int(w) for w in wires))
    original = Operator(raw).data
    circuit = q.from_qiskit(raw)
    exported = circuit.to_qiskit()
    np.testing.assert_allclose(Operator(exported).data, original, atol=1e-12, rtol=0)
    np.testing.assert_allclose(Operator(circuit.inverse().to_qiskit()).data,
                               original.conj().T, atol=1e-12, rtol=0)
    np.testing.assert_allclose(Operator(circuit.decompose().to_qiskit()).data,
                               original, atol=1e-12, rtol=0)
    np.testing.assert_allclose(Operator(circuit.compose(circuit.inverse()).to_qiskit()).data,
                               np.eye(8), atol=1e-12, rtol=0)
    exported.z(0)
    np.testing.assert_allclose(Operator(circuit.to_qiskit()).data, original, atol=1e-12, rtol=0)


def test_exported_phase_remains_observable_under_control():
    raw = QuantumCircuit(1, global_phase=np.pi)
    exported = q.from_qiskit(raw).to_qiskit()
    np.testing.assert_allclose(Operator(exported.to_gate().control()).data,
                               Operator(raw.to_gate().control()).data, atol=1e-12, rtol=0)
    assert not np.allclose(Operator(exported.to_gate().control()).data, np.eye(4))


@pytest.mark.parametrize("kind", ["measurement", "reset", "rotation", "metadata"])
def test_reject_unsupported_imports(kind):
    raw = QuantumCircuit(1, 1) if kind == "measurement" else QuantumCircuit(1)
    if kind == "measurement":
        raw.measure(0, 0)
    elif kind == "reset":
        raw.reset(0)
    elif kind == "rotation":
        raw.rx(0.2, 0)
    else:
        raw.metadata = {"example": True}
    with pytest.raises(q.UnsupportedOperation):
        q.from_qiskit(raw)


def test_trace_budget_rejects_before_execution():
    c = q.Circuit(2).gates.h(0).gates.cx(0, 1)
    with pytest.raises(q.ResourceLimit):
        c.debug.trace(max_steps=1)
    with pytest.raises(q.ResourceLimit):
        c.debug.trace(max_bytes=16 * 4 * 3 - 1)
    assert len(c.debug.trace(max_steps=2, max_bytes=16 * 4 * 3)) == 3
