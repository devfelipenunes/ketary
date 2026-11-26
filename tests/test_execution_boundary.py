"""Native ideal execution and shared monotonic trace invariants."""
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import ketary as q

@pytest.mark.parametrize("initial",[None,"101","array","snapshot"])
def test_execution_preserves_full_complex_state(initial):
    native=QuantumCircuit(3,global_phase=.37)
    native.h(2)
    native.ry(.51,0)
    native.cx(2,0)
    native.s(1)
    c=q.from_qiskit(native)
    vector=np.array([1,2j,3,-4j,2,1j,0,1],dtype=complex)
    vector/=np.linalg.norm(vector)
    if initial is None:
        expected=Statevector.from_instruction(native)
        value=None
    elif initial=="101":
        expected=Statevector.from_label(initial).evolve(native)
        value=initial
    else:
        expected=Statevector(vector).evolve(native)
        value=q.Result(vector) if initial=="snapshot" else vector
    observed=c.run(initial_state=value,max_bytes=128)
    np.testing.assert_allclose(observed.math.statevector(),expected.data,atol=1e-12,rtol=0)
    assert c.to_qiskit()==native

def test_budget_preflight_before_native_call(monkeypatch):
    import ketary._execution as execution
    c=q.bell()
    def fail(*a,**k):
        pytest.fail("native execution must not start")
    monkeypatch.setattr(execution,"execute_ideal",fail)
    with pytest.raises(q.ResourceLimit):
        c.run(max_bytes=63)
    with pytest.raises(q.UnsupportedOperation):
        c.run(mode="other")

def test_shared_trace_matches_native_prefixes_and_stops_early(monkeypatch):
    import ketary._trace as trace
    native=QuantumCircuit(3,global_phase=.41)
    native.h(2)
    native.cx(2,0)
    native.rz(.31,0)
    c=q.from_qiskit(native)
    steps=c.debug.trace()
    for index,step in enumerate(steps):
        prefix=QuantumCircuit(3,global_phase=.41)
        for item in native.data[:index]:
            prefix.append(item.operation,[native.find_bit(w).index for w in item.qubits])
        expected=Statevector.from_instruction(prefix).data
        np.testing.assert_allclose(step.result.math.statevector(),expected,atol=1e-12,rtol=0)
        c.debug.checkpoint(index).result.test.state(step.result,ignore_global_phase=False).require()
    original=trace._Cursor.at
    indices=[]
    def tracked(self,index):
        indices.append(index)
        return original(self,index)
    monkeypatch.setattr(trace._Cursor,"at",tracked)
    reference=q.Circuit(1).h(0).x(0).x(0)
    observed=q.Circuit(1).h(0).z(0).z(0)
    assert observed.debug.compare(reference).step_index==2
    assert indices==[0,0,1,1,2,2]
