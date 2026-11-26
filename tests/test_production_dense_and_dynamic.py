"""Independent dense mathematical oracles and expanded execution budget regressions."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from scipy.linalg import expm

@pytest.mark.parametrize("n",[1,2,3,4])
@pytest.mark.parametrize("seed",range(4))
def test_arbitrary_state_preparation(n,seed):
    rng=np.random.default_rng(seed+101)
    v=rng.normal(size=2**n)+1j*rng.normal(size=2**n)
    v/=np.linalg.norm(v)
    c=q.Circuit.prepare_state(v,seed=seed)
    np.testing.assert_allclose(c.run().math.statevector(),v,atol=1e-9,rtol=0)
    U=Operator(c.to_qiskit()).data
    np.testing.assert_allclose(U.conj().T@U,np.eye(2**n),atol=1e-9,rtol=0)
    np.testing.assert_allclose(c.inverse().run(initial_state=v).math.statevector(),np.eye(2**n)[:,0],atol=1e-9,rtol=0)

@pytest.mark.parametrize("n",[1,2,3])
@pytest.mark.parametrize("seed",range(4))
def test_arbitrary_unitary(n,seed):
    rng=np.random.default_rng(seed+202)
    z=rng.normal(size=(2**n,2**n))+1j*rng.normal(size=(2**n,2**n))
    u,r=np.linalg.qr(z)
    u=u@np.diag(np.diag(r)/abs(np.diag(r)))*np.exp(.37j)
    c=q.Circuit.from_unitary(u,seed=seed)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,u,atol=1e-9,rtol=0)
    v=rng.normal(size=2**n)+1j*rng.normal(size=2**n);v/=np.linalg.norm(v)
    np.testing.assert_allclose(c.run(initial_state=v).math.statevector(),u@v,atol=1e-9,rtol=0)

@pytest.mark.parametrize("n",[1,2,3])
@pytest.mark.parametrize("t",[-.8,.0,.23,.9])
def test_noncommuting_exact_dense_evolution(n,t):
    x=np.array([[0,1],[1,0]],complex);z=np.diag([1,-1]);y=np.array([[0,-1j],[1j,0]])
    I=np.eye(2**n)
    H=q.X(0)+.7*q.Z(0)+.31*q.I(n-1)
    matrix=np.kron(np.eye(2**(n-1)),x+.7*z)+.31*I
    if n>1:
        H=H+.24*(q.Y(n-1)@q.X(0))
        matrix=matrix+.24*np.kron(y,np.kron(np.eye(2**(n-2)),x))
    c=q.Circuit(n).evolve_exact(H,time=t)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expm(-1j*t*matrix),atol=1e-9,rtol=0)

@pytest.mark.parametrize("values",[[0,0],[1,1],[1],[1,0,0],[float("nan"),0],["1",0],[True,0],{0,1}])
def test_preparation_invalid(values):
    with pytest.raises((ValueError,TypeError)):q.Circuit.prepare_state(values)

@pytest.mark.parametrize("matrix",[[[1,0],[0,2]],[[1,0],[0]],[[1,0,0],[0,1,0],[0,0,1]],[[1,float("inf")],[0,1]],[[1]],"matrix"])
def test_matrix_invalid(matrix):
    with pytest.raises((ValueError,TypeError)):q.Circuit.from_unitary(matrix)

def test_bounded_iterable_and_atomic_dense_evolve():
    with pytest.raises(q.ResourceLimit):q.Circuit.prepare_state(itertools.repeat(1))
    with pytest.raises(q.ResourceLimit):q.Circuit.from_unitary(itertools.repeat([1,0]))
    with pytest.raises(q.ResourceLimit):q.Circuit.from_unitary([itertools.repeat(1),[0,1]])
    c=q.bell();before=c.to_qiskit()
    for H,t in [(q.X(2),.3),(q.X(0),float("inf")),(object(),.2)]:
        with pytest.raises((ValueError,TypeError)):c.evolve_exact(H,time=t)
        assert c.to_qiskit()==before
    with pytest.raises(q.ResourceLimit):q.Circuit(6).evolve_exact(q.X(0),time=.2)
    with pytest.raises(q.UnsupportedOperation):q.Circuit.classical(1,1).evolve_exact(q.X(0),time=.2)

def test_dynamic_expanded_budget_import_and_after_mutation():
    raw=QuantumCircuit(1,1)
    raw.measure(0,0)
    with raw.if_test((raw.clbits[0],1)):
        for _ in range(1019):raw.x(0)
    raw.x(0)
    c=q.Circuit.from_dynamic(raw)
    # 1022 expanded instructions, three later gates exceed limit.
    c.x(0).x(0).x(0)
    with pytest.raises(q.ResourceLimit,match="expanded"):c.run_shots(shots=1)
    with pytest.raises(q.ResourceLimit,match="expanded"):q.Circuit.from_dynamic(c.to_qiskit())

def test_dynamic_count_failure_multiple_registers(monkeypatch):
    import sys,types,qiskit
    from qiskit import QuantumRegister,ClassicalRegister
    raw=QuantumCircuit(QuantumRegister(2),ClassicalRegister(1,"a"),ClassicalRegister(1,"b"))
    raw.measure([0,1],[0,1])
    c=q.Circuit.from_dynamic(raw)
    class FakeBackend:
        def __init__(self,**kw):pass
        def run(self,*a,**kw):return self
        def result(self):return types.SimpleNamespace(success=True,get_counts=lambda:{"01":8})
    fake=types.ModuleType("qiskit_aer");fake.AerSimulator=FakeBackend
    monkeypatch.setitem(sys.modules,"qiskit_aer",fake)
    monkeypatch.setattr(qiskit,"transpile",lambda circuit,**kw:circuit)
    with pytest.raises(RuntimeError,match="register-separated"):c.run_shots(shots=8)
