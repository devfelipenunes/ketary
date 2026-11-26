"""Strict oracles for research-only abstraction primitives."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from scipy.linalg import expm
from research import abstraction_primitives as p

def matrix(c):return Operator(c.to_qiskit()).data
def same(a,b):
    np.testing.assert_allclose(a,b,atol=1e-9,rtol=0)
def pauli(label):
    m={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),"Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}
    out=np.array([[1.]])
    for x in label:out=np.kron(out,m[x])
    return out

@pytest.mark.parametrize("label",["I","X","Y","Z","III","XYZ","YIX","ZZZ","IYY"])
@pytest.mark.parametrize("theta",[-.71,0.,1.23])
def test_pauli_rotation(label,theta):
    same(matrix(p.pauli_rotation(label,theta)),expm(-1j*theta/2*pauli(label)))

@pytest.mark.parametrize("time",[-.31,0.,.7])
def test_commuting_hamiltonian_with_identity(time):
    terms={"XX":.7,"YY":-.31,"ZZ":.21,"II":.9}
    h=sum(v*pauli(k) for k,v in terms.items())
    same(matrix(p.evolve(q.Observable(terms),time)),expm(-1j*time*h))

def test_noncommuting_is_explicit_and_converges():
    H=q.X(0)+.7*q.Z(0)
    target=expm(-.7j*(pauli("X")+.7*pauli("Z")))
    with pytest.raises(q.UnsupportedOperation):p.evolve(H,.7)
    for order in (1,2):
        errors=[np.linalg.norm(matrix(p.product_formula(H,.7,steps=s,order=order))-target) for s in (1,4,16)]
        assert errors[0]>errors[1]>errors[2]
    assert np.linalg.norm(matrix(p.product_formula(H,.7,steps=8,order=2))-target)<np.linalg.norm(matrix(p.product_formula(H,.7,steps=8))-target)

@pytest.mark.parametrize("gate",["cp","crx","cry","crz","rxx","ryy","rzz"])
def test_aligned_angle_order_and_atomicity(gate):
    c=q.Circuit(3).h(2);before=matrix(c)
    pairs=[(2,0),(1,2),(2,0)]
    angles=[.13,-.42,.71]
    result=p.aligned(c,gate,angles,pairs)
    native=c.to_qiskit()
    for t,(a,b) in zip(angles,pairs):getattr(native,gate)(t,a,b)
    same(matrix(result),Operator(native).data);same(matrix(c),before)
    with pytest.raises(ValueError):p.aligned(c,gate,[.1,float("nan"),.3],pairs)
    same(matrix(c),before)

def test_symbolic_identity_and_sequential_layers():
    theta=q.Circuit.parameter("theta");phi=q.Circuit.parameter("phi")
    base=q.Circuit.symbolic(2).h(0)
    result=p.aligned(base,"crx",[theta,phi],[(0,1),(1,0)])
    assert set(result.parameters)=={theta,phi};assert not base.parameters
    rows=[[.2,.3],[.5,-.2]]
    out=p.layers(result,rows)
    expected=q.Circuit(2)
    for row in rows:expected.apply(result.bind(row))
    same(matrix(out),matrix(expected))
    with pytest.raises(ValueError):p.layers(result,[[.2,.3],[.4]])
    assert set(result.parameters)=={theta,phi}

@pytest.mark.parametrize("k",[-3,-1,0,1,4])
def test_power_strict_phase(k):
    native=QuantumCircuit(2,global_phase=.37);native.h(1);native.cx(1,0)
    c=q.from_qiskit(native)
    same(matrix(p.power(c,k)),np.linalg.matrix_power(Operator(native).data,k))

@pytest.mark.parametrize("controls",[1,2])
def test_controlled_relative_phase(controls):
    native=QuantumCircuit(1,global_phase=.731);native.ry(.31,0)
    U=Operator(native).data;n=1+controls;d=1<<n
    target=np.eye(d,dtype=complex);idx=[(i<<controls)+(1<<controls)-1 for i in range(2)]
    target[np.ix_(idx,idx)]=U
    same(matrix(p.controlled(q.from_qiskit(native),controls)),target)
    # A global-phase-only block must still have observable relative phase.
    pure=QuantumCircuit(1,global_phase=.731)
    expected=np.eye(d,dtype=complex);expected[idx,idx]=np.exp(.731j)
    same(matrix(p.controlled(q.from_qiskit(pure),controls)),expected)

@pytest.mark.parametrize("n",[1,2,3,4])
def test_reflection(n):
    u=q.Circuit(n).ry(.3,0)
    if n>1:u.cx(0,n-1)
    psi=matrix(u)[:,0]
    same(matrix(p.reflection(u)),2*np.outer(psi,psi.conj())-np.eye(1<<n))

@pytest.mark.parametrize("n",range(1,7))
def test_increment_full_truth_table(n):
    ref=np.zeros((1<<n,1<<n))
    for i in range(1<<n):ref[(i+1)%(1<<n),i]=1
    same(matrix(p.increment(n)),ref)

def test_sequence_tensor_and_parity():
    a=q.bell();b=q.Circuit(1).ry(.3,0)
    same(matrix(p.tensor(a,b)),np.kron(matrix(b),matrix(a)))
    c=p.parity(4,[2,0],3);ref=np.zeros((16,16))
    for x in range(16):ref[x^((((x>>2)&1)^(x&1))<<3),x]=1
    same(matrix(c),ref)
    with pytest.raises(ValueError):p.parity(4,[2,0],2)
    with pytest.raises(ValueError):p.sequence(3,[(a,[0,0])])

def test_conjugation_not_cleanup_claim():
    u=q.Circuit(2).cx(0,1);v=q.Circuit(1).z(0)
    c=p.conjugate(u,v,n=2,compute_wires=[0,1],action_wires=[1])
    expected=matrix(u).conj().T@np.kron(pauli("Z"),np.eye(2))@matrix(u)
    same(matrix(c),expected)

def test_graph_state_analytic_phase():
    c=p.graph_state(3,[(0,2),(2,1)])
    ref=np.array([(-1)**(((x&1)*((x>>2)&1))+(((x>>2)&1)*((x>>1)&1))) for x in range(8)])/np.sqrt(8)
    same(c.run().math.statevector(),ref)
    with pytest.raises(ValueError):p.graph_state(3,[(0,2),(2,0)])
    same(p.basis("101").run().math.statevector(),np.eye(8)[5])

def test_bounds_and_no_construction_execution(monkeypatch):
    def forbidden(*a,**k):pytest.fail("implicit execution")
    monkeypatch.setattr(q.Circuit,"run",forbidden)
    p.evolve(q.X(0),.2)
    p.controlled(q.bell())
    with pytest.raises(q.ResourceLimit):p.power(q.bell(),65)
    with pytest.raises(q.ResourceLimit):p.controlled(q.Circuit(5))
    with pytest.raises(q.ResourceLimit):p.product_formula(q.X(0),.2,steps=33)

@pytest.mark.parametrize("fault,expected",[(None,"00"),(0,"01"),(1,"11"),(2,"10")])
def test_syndrome_dynamic(fault,expected):
    pytest.importorskip("qiskit_aer")
    result=p.syndrome_bit_flip(fault).run_shots(shots=32,seed=1101)
    assert result.counts=={expected:32}

def test_feedforward_dynamic():
    pytest.importorskip("qiskit_aer")
    assert p.feedforward().run_shots(shots=32,seed=1101).counts=={"11":32}
