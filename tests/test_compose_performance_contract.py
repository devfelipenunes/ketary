import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import ketary as q

def test_composition_closed_and_phase(monkeypatch):
    a=QuantumCircuit(3,global_phase=.27); a.h(1); a.rx(.4,2)
    b=QuantumCircuit(2,global_phase=.61); b.cx(1,0); b.ry(.8,0)
    x,y=q.from_qiskit(a),q.from_qiskit(b)
    import ketary._circuit as internal
    def fail(*args): raise AssertionError("unnecessary full scan")
    monkeypatch.setattr(internal,"_validate",fail)
    z=x.compose(y,wires=[2,0])
    np.testing.assert_allclose(Operator(z.to_qiskit()).data,Operator(a.compose(b,qubits=[2,0])).data,atol=1e-12,rtol=0)
    z.gates.z(0)
    assert x.to_qiskit()==a and y.to_qiskit()==b

def test_composition_rejects_invalid_mapping():
    c=q.bell()
    for wires in ([0,0],[0,2],[0],[-1,1]):
        with pytest.raises(ValueError): c.compose(c,wires=wires)

@pytest.mark.parametrize("a",[[float("inf"),0],[float("nan"),0],[1.001,0]])
def test_snapshot_still_validated(a):
    with pytest.raises(ValueError): q.Result(a)
