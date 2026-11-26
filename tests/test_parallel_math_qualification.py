"""Independent time derivatives, disjoint block tensors and unitary preparation."""
import itertools
import numpy as np
import pytest
import ketary as q
from scipy.linalg import expm
from qiskit import QuantumCircuit
from qiskit.circuit.library import StatePreparation
from qiskit.quantum_info import Operator,Statevector

X=np.array([[0,1],[1,0]],complex)
Y=np.array([[0,-1j],[1j,0]],complex)
Z=np.diag([1.,-1.])
I=np.eye(2)
H=(X+Z)/np.sqrt(2)

@pytest.mark.parametrize("seed",range(12))
@pytest.mark.parametrize("t",[-.71,0.,.43])
def test_commuting_hamiltonian_time_derivative(seed,t):
    rng=np.random.default_rng(28400+seed)
    a,b,c,d=map(float,rng.uniform(-1,1,4))
    M=a*np.eye(4)+b*np.kron(Z,I)+c*np.kron(I,Z)+d*np.kron(Z,Z)
    obs=q.Observable({"II":a,"ZI":b,"IZ":c,"ZZ":d})
    v=rng.normal(size=4)+1j*rng.normal(size=4);v/=np.linalg.norm(v)
    p=q.Circuit.parameter("t")
    template=q.Circuit.symbolic(2).evolve(obs,time=p)
    before=template.to_qiskit()
    U=expm(-1j*t*M);expected=U@v
    native=QuantumCircuit(2,global_phase=-a*t)
    native.rz(2*c*t,0);native.rz(2*b*t,1);native.rzz(2*d*t,0,1)
    bound=template.bind({p:t})
    np.testing.assert_allclose(Operator(bound.to_qiskit()).data,U,atol=1e-9,rtol=0)
    np.testing.assert_allclose(Operator(native).data,U,atol=1e-9,rtol=0)
    eps=1e-5
    def state(s):return template.bind({p:s}).run(initial_state=v).math.statevector()
    np.testing.assert_allclose(state(t),expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose((state(t+eps)-state(t-eps))/(2*eps),-1j*M@expected,atol=1e-8,rtol=0)
    # Jacobian uses zero-state preparation, so prepare |++> explicitly.
    circuit=q.Circuit.symbolic(2).h([0,1]).evolve(obs,time=p)
    psi=U@(np.ones(4)/2)
    matrices=[np.kron(I,X),np.kron(Y,X),np.kron(Z,Z)]
    want=[float((1j*np.vdot(psi,(M@o-o@M)@psi)).real) for o in matrices]
    np.testing.assert_allclose(circuit.expectation_jacobian({p:t},[q.X(0),q.Y(1)@q.X(0),q.Z(1)@q.Z(0)]),np.array(want)[:,None],atol=1e-9,rtol=0)
    assert template.to_qiskit()==before

def test_time_derivative_phase_and_noncommuting_preflight(monkeypatch):
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(1).h(0).evolve(3*q.I(),time=t)
    np.testing.assert_allclose(c.bind({t:.2}).run().math.statevector(),np.exp(-.6j)*np.ones(2)/np.sqrt(2),atol=1e-9,rtol=0)
    before=c.to_qiskit()
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**kw:pytest.fail("unexpected run"))
    assert c.expectation_jacobian({t:.2},[q.X(0)])==((0.,),)
    with pytest.raises(q.UnsupportedOperation):c.evolve(q.X(0)+q.Z(0),time=t)
    assert c.to_qiskit()==before

@pytest.mark.parametrize("wires",list(itertools.permutations(range(3))))
@pytest.mark.parametrize("theta",[-.8,.31])
def test_disjoint_tensor_with_wire_permutation(wires,theta):
    a=q.Circuit(1).ry(theta,0).evolve(q.I(),time=.19)
    b=q.Circuit(2).h(0).cx(0,1).evolve(q.I(1),time=-.37)
    a0=a.to_qiskit();b0=b.to_qiskit()
    R=np.cos(theta/2)*I-1j*np.sin(theta/2)*Y
    C=np.zeros((4,4),complex)
    for j in range(4):C[j^((j&1)<<1),j]=1
    canonical=np.exp(.18j)*np.kron(C@np.kron(I,H),R)
    perm=np.zeros((8,8))
    for j in range(8):perm[sum(((j>>k)&1)<<w for k,w in enumerate(wires)),j]=1
    expected=perm@canonical@perm.T
    c=q.Circuit(3).apply(a,wires=[wires[0]]).apply(b,wires=wires[1:])
    ref=QuantumCircuit(3);ref.compose(a0,qubits=[wires[0]],inplace=True);ref.compose(b0,qubits=list(wires[1:]),inplace=True)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose(Operator(ref).data,expected,atol=1e-9,rtol=0)
    v=np.arange(1,9)+1j*np.arange(8);v=v/np.linalg.norm(v)
    np.testing.assert_allclose(c.run(initial_state=v).math.statevector(),expected@v,atol=1e-9,rtol=0)
    assert a.to_qiskit()==a0 and b.to_qiskit()==b0
    before=c.to_qiskit()
    with pytest.raises(ValueError):c.apply(b,wires=[0,0])
    assert c.to_qiskit()==before

@pytest.mark.parametrize("n",[1,2,3,4,5])
@pytest.mark.parametrize("seed",[28801,28802,28803])
def test_state_preparation_unitary_extension(n,seed):
    rng=np.random.default_rng(seed+n)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    c=q.Circuit.prepare_state(v,seed=seed)
    raw=QuantumCircuit(n);raw.append(StatePreparation(v,normalize=False),range(n))
    M=Operator(raw).data;got=Operator(c.to_qiskit()).data
    np.testing.assert_allclose(got,M,atol=1e-9,rtol=0)
    np.testing.assert_allclose(got[:,0],v,atol=1e-9,rtol=0)
    np.testing.assert_allclose(got.conj().T@got,np.eye(1<<n),atol=1e-9,rtol=0)
    w=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);w/=np.linalg.norm(w)
    out=c.run(initial_state=w).math.statevector()
    np.testing.assert_allclose(out,M@w,atol=1e-9,rtol=0)
    np.testing.assert_allclose(c.inverse().run(initial_state=out).math.statevector(),w,atol=1e-9,rtol=0)

def test_preparation_product_and_rejection():
    a=np.array([.6,.8j]);b=np.array([1,1j])/np.sqrt(2)
    v=np.kron(b,a)
    np.testing.assert_allclose(q.Circuit.prepare_state(v).run().math.statevector(),v,atol=1e-9,rtol=0)
    for invalid in ([1,1],[1,0,0],[float("nan"),0]):
        with pytest.raises(ValueError):q.Circuit.prepare_state(invalid)
    with pytest.raises(q.ResourceLimit):q.Circuit.prepare_state([1]+[0]*63)
