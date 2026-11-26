"""L0 gate semantics, independent matrix fixtures and input isolation."""
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import RXGate, CCXGate, CZGate
from qiskit.quantum_info import Operator, Statevector
import ketary as q

X=np.array([[0,1],[1,0]],complex)
Y=np.array([[0,-1j],[1j,0]],complex)
Z=np.diag([1,-1]).astype(complex)

@pytest.mark.parametrize("name,matrix",[
    ("y",Y),("s",np.diag([1,1j])),("sdg",np.diag([1,-1j])),
    ("t",np.diag([1,np.exp(1j*np.pi/4)])),
    ("tdg",np.diag([1,np.exp(-1j*np.pi/4)])),
])
def test_single_gate_matrix(name,matrix):
    c=q.Circuit(1); assert getattr(c.gates,name)(0) is c
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,matrix,rtol=0,atol=1e-12)
    np.testing.assert_allclose(Operator(c.inverse().to_qiskit()).data,matrix.conj().T,rtol=0,atol=1e-12)

@pytest.mark.parametrize("name,pauli",[("rx",X),("ry",Y),("rz",Z)])
@pytest.mark.parametrize("theta",[0.0,.37,-np.pi,2*np.pi])
def test_rotation_matrix(name,pauli,theta):
    c=q.Circuit(1); getattr(c.gates,name)(theta,0)
    expected=np.cos(theta/2)*np.eye(2)-1j*np.sin(theta/2)*pauli
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,rtol=0,atol=1e-12)
    imported=q.from_qiskit(c.to_qiskit())
    np.testing.assert_allclose(Operator(imported.inverse().to_qiskit()).data,expected.conj().T,rtol=0,atol=1e-12)

def test_controlled_gates_and_wires():
    c=q.Circuit(2).gates.cz(1,0)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,np.diag([1,1,1,-1]),atol=1e-12)
    c=q.Circuit(3).gates.ccx(2,0,1)
    expected=np.eye(8); expected[:,[5,7]]=expected[:,[7,5]]
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,atol=1e-12)

@pytest.mark.parametrize("bad",[float("nan"),float("inf"),True,1j,"0.5",Parameter("theta")])
def test_bad_rotation_is_atomic(bad):
    c=q.bell(); before=c.to_qiskit()
    with pytest.raises(ValueError): c.gates.rx(bad,0)
    assert c.to_qiskit()==before

def test_append_copy_and_rejection():
    c=q.Circuit(3); gate=RXGate(.37)
    assert c.append(gate,[2]) is c
    expected=Operator(c.to_qiskit()).data.copy()
    gate.params=[.89]
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,atol=1e-12)
    before=c.to_qiskit()
    for gate,wires in [(RXGate(.1),[0,1]),(CCXGate(),[0,0,1]),(CZGate(ctrl_state=0),[0,1])]:
        with pytest.raises(ValueError): c.append(gate,wires)
        assert c.to_qiskit()==before

def test_extended_roundtrip_trace_and_inverse():
    c=q.Circuit(3).gates.h(0).gates.y(2).gates.s(0).gates.t(1).gates.rx(.3,1).gates.ry(-.6,0).gates.rz(.7,2).gates.cz(0,2).gates.ccx(0,2,1)
    native=c.to_qiskit()
    d=q.from_qiskit(native)
    np.testing.assert_allclose(d.debug.trace()[-1].result.math.statevector(),Statevector.from_instruction(native).data,atol=1e-12)
    np.testing.assert_allclose(Operator(d.compose(d.inverse()).to_qiskit()).data,np.eye(8),atol=1e-12)
