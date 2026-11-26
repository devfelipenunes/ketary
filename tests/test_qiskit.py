import numpy as np
import pytest
# A missing required backend must fail collection, not silently skip.
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import ketary as q
BELL=np.array([1,0,0,1])/np.sqrt(2)

def test_single_api():
    raw=QuantumCircuit(2); raw.h(0); raw.cx(0,1)
    for c in (q.bell(),q.Circuit(2).gates.h(0).gates.cx(0,1),q.from_qiskit(raw)):
        assert type(c) is q.Circuit
        np.testing.assert_allclose(c.run().math.statevector(),BELL,atol=1e-12)

def test_ghz():
    expected=np.zeros(8); expected[[0,7]]=1/np.sqrt(2)
    np.testing.assert_allclose(q.ghz(3).run().math.statevector(),expected,atol=1e-12)

def test_import_export_isolation():
    raw=q.bell().to_qiskit(); c=q.from_qiskit(raw); raw.x(0); exported=c.to_qiskit(); exported.z(0)
    np.testing.assert_allclose(c.run().math.statevector(),BELL,atol=1e-12)

def test_compose_inverse():
    a=q.bell(); b=q.Circuit(1).gates.z(0); d=a.compose(b,wires=[0])
    assert d.run().test.fidelity(BELL).status=="FAIL"
    np.testing.assert_allclose(a.run().math.statevector(),BELL,atol=1e-12)
    np.testing.assert_allclose(a.compose(a.inverse()).run().math.statevector(),[1,0,0,0],atol=1e-12)

def test_trace_phase_mapping():
    raw=QuantumCircuit(3,global_phase=.2); raw.h(2); raw.cx(2,0); raw.swap(0,1)
    c=q.from_qiskit(raw); trace=c.debug.trace()
    assert trace[-1].wires==(0,1)
    np.testing.assert_allclose(trace[-1].result.math.statevector(),Statevector.from_instruction(raw).data,atol=1e-12)

def test_result_reuse(monkeypatch):
    c=q.bell(); r=c.run(); c.gates.z(0)
    def fail(*args,**kwargs): raise AssertionError("re-execution")
    monkeypatch.setattr(q.Circuit,"run",fail)
    r.test.fidelity(BELL).require(); r.sample(shots=10,seed=1); r.math.probabilities()

def test_invalid_and_unsupported():
    c=q.bell(); before=len(c.to_qiskit().data)
    with pytest.raises(ValueError): c.gates.cx(0,0)
    assert len(c.to_qiskit().data)==before
    raw=QuantumCircuit(1,1); raw.measure(0,0)
    with pytest.raises(q.UnsupportedOperation): q.from_qiskit(raw)
    with pytest.raises(q.ResourceLimit): c.run(max_bytes=1)

def test_decompose_swap():
    c=q.Circuit(2).gates.x(0).gates.swap(0,1); d=c.decompose()
    assert "swap" in c.to_qiskit().count_ops() and "swap" not in d.to_qiskit().count_ops()
    np.testing.assert_allclose(c.run().math.statevector(),d.run().math.statevector(),atol=1e-12)

def test_open_control_rejected():
    from qiskit.circuit.library import CXGate
    raw=QuantumCircuit(2); raw.append(CXGate(ctrl_state=0),[0,1])
    with pytest.raises(q.UnsupportedOperation):
        q.from_qiskit(raw)

def test_trace_qubit_limit():
    with pytest.raises(q.ResourceLimit):
        q.Circuit(9).debug.trace()

def test_transform_source_isolation():
    a=q.bell(); b=q.Circuit(1).gates.z(0)
    for d in (a.compose(b,wires=[1]),a.inverse(),a.decompose()):
        d.gates.x(0)
        np.testing.assert_allclose(a.run().math.statevector(),BELL,atol=1e-12)
    np.testing.assert_allclose(b.run().math.statevector(),[1,0],atol=1e-12)

def test_trace_snapshot_independent():
    c=q.bell(); steps=c.debug.trace(); c.gates.z(0)
    np.testing.assert_allclose(steps[-1].result.math.statevector(),BELL,atol=1e-12)

def test_reversed_wire_mapping():
    a=q.Circuit(3); b=q.Circuit(2).gates.x(0).gates.cx(0,1)
    d=a.compose(b,wires=[2,0])
    expected=np.zeros(8); expected[5]=1
    np.testing.assert_allclose(d.run().math.statevector(),expected,atol=1e-12)

@pytest.mark.parametrize("bad",[-1,2,True,1.5])
def test_invalid_wire_atomic(bad):
    c=q.bell(); before=c.to_qiskit()
    with pytest.raises(ValueError):
        c.gates.h(bad)
    assert c.to_qiskit()==before
