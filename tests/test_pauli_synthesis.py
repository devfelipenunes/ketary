"""CH15: optimize mixed Pauli Y basis changes without phase drift."""
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator
from qiskit import transpile
from scipy.linalg import expm
from research.abstraction_primitives import pauli_rotation as previous

P={"I":np.eye(2,dtype=complex),"X":np.array([[0,1],[1,0]],complex),"Y":np.array([[0,-1j],[1j,0]],complex),"Z":np.diag([1.,-1.])}
def matrix(label):
    out=np.array([[1]],complex)
    for axis in label:out=np.kron(out,P[axis])
    return out

@pytest.mark.parametrize("label",["XY","YZ","YX","XYZ","YYY","IYYZ","YIYX","ZYYX"])
@pytest.mark.parametrize("t",[-.37,.81])
def test_mixed_y_exact_and_lower_gate_count(label,t):
    n=len(label)
    old=previous(label,2*t).to_qiskit()
    c=q.Circuit(n).evolve(q.Observable({label:1.}),time=t)
    new=c.to_qiskit()
    expected=expm(-1j*t*matrix(label))
    np.testing.assert_allclose(Operator(new).data,expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose(Operator(old).data,expected,atol=1e-9,rtol=0)
    assert len(new.data)==len(old.data)-2*label.count("Y")
    for raw in (old,new):
        expanded=transpile(raw,basis_gates=["u","cx"],optimization_level=0,qubits_initially_zero=False)
        np.testing.assert_allclose(Operator(expanded).data,expected,atol=1e-9,rtol=0)
    assert len(transpile(new,basis_gates=["u","cx"],optimization_level=0).data)<len(transpile(old,basis_gates=["u","cx"],optimization_level=0).data)

def test_symbolic_mixed_y_and_identity():
    t=q.Circuit.parameter("t")
    H=q.Observable({"YZX":.7,"III":.9})
    c=q.Circuit.symbolic(3).evolve(H,time=t)
    bound=c.bind({t:.31})
    expected=expm(-.31j*(.7*matrix("YZX")+.9*np.eye(8)))
    np.testing.assert_allclose(Operator(bound.to_qiskit()).data,expected,atol=1e-9,rtol=0)
