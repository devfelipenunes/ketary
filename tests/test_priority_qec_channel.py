"""Exact IID bit/phase flip channel versus analytic repetition-code logical error."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix,Kraus

I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],complex)
Z=np.diag([1.,-1.]).astype(complex)

def noise(p,phase):
    matrices=[]
    for bits in itertools.product((0,1),repeat=3):
        weight=p**sum(bits)*(1-p)**(3-sum(bits))
        op=np.array([[1.]],complex)
        for bit in reversed(bits):
            op=np.kron(op,(Z if phase else X) if bit else I)
        matrices.append(np.sqrt(weight)*op)
    return Kraus(matrices)

def encode(c,theta,phi,phase):
    c.ry(theta,0);c.rz(phi,0);c.cx(0,1);c.cx(0,2)
    if phase:
        for wire in range(3):c.h(wire)
    return c

def decode(c,phase):
    if phase:
        for wire in range(3):c.h(wire)
    c.cx(0,2);c.cx(0,1);c.ccx(1,2,0)
    return c

@pytest.mark.parametrize("p",[0.,.03,.15,.5,1.])
@pytest.mark.parametrize("phase",[False,True])
@pytest.mark.parametrize("theta,phi",[(0.,0.),(.83,-1.17)])
def test_repetition_channel(p,phase,theta,phi):
    channel=noise(p,phase)
    state=encode(q.Circuit(3),theta,phi,phase).run_channel(channel)
    decoded=decode(q.Circuit(3),phase).run_density(initial_state=state)
    native=DensityMatrix.from_instruction(encode(QuantumCircuit(3),theta,phi,phase)).evolve(channel).evolve(decode(QuantumCircuit(3),phase))
    np.testing.assert_allclose(decoded.data,native.data,atol=1e-9,rtol=0)
    logical=sum(decoded.data[2*i:2*i+2,2*i:2*i+2] for i in range(4))
    v=np.array([np.exp(-.5j*phi)*np.cos(theta/2),np.exp(.5j*phi)*np.sin(theta/2)])
    rho=np.outer(v,v.conj())
    fail=3*p*p-2*p**3
    expected=(1-fail)*rho+fail*X@rho@X
    np.testing.assert_allclose(logical,expected,atol=1e-9,rtol=0)
    assert np.vdot(v,logical@v).real==pytest.approx(np.vdot(v,expected@v).real,abs=1e-9)
