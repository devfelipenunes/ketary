import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import ketary as q

def test_logical_lowering_phase_and_isolation():
    native=QuantumCircuit(2,global_phase=.42)
    native.h(0); native.swap(0,1)
    c=q.from_qiskit(native)
    lowered=c.transpile(basis_gates=["h","cx"])
    assert set(lowered.to_qiskit().count_ops())=={"h","cx"}
    np.testing.assert_allclose(Operator(native).data,Operator(lowered.to_qiskit()).data,rtol=0,atol=1e-12)
    assert c.to_qiskit()==native
    lowered.gates.x(0)
    assert c.to_qiskit()==native

@pytest.mark.parametrize("basis",[[],["cx","cx"],["u"],"h"])
def test_bad_basis(basis):
    with pytest.raises(ValueError): q.bell().transpile(basis_gates=basis)

def test_limits_and_incompatible_basis():
    with pytest.raises(q.ResourceLimit): q.Circuit(9).transpile(basis_gates=["h","cx"])
    with pytest.raises(ValueError): q.bell().transpile(basis_gates=["h","cx"],seed=-1)
    with pytest.raises(q.UnsupportedOperation): q.bell().transpile(basis_gates=["x"])
