"""Compare reuse with explicit placement and an independent bit-index oracle."""
import numpy as np
import pytest
import ketary as q
from scipy.linalg import expm
from research.observable_reuse import embed as prototype

def embed(H,wires,*,width):
    return H.on(wires,width=width)

def local_evolution(c,H,time,*,wires):
    return c.evolve(H.on(wires,width=c.num_qubits),time=time)
from qiskit.quantum_info import Operator
P={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),"Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}
def dense_local(H):
    out=0
    for label,coef in H.to_dict().items():
        term=np.array([[1.]])
        for axis in label:term=np.kron(term,P[axis])
        out=out+coef*term
    return out
def lift(m,wires,n):
    out=np.zeros((1<<n,1<<n),complex)
    mask=sum(1<<w for w in wires)
    for i in range(1<<n):
        a=sum(((i>>w)&1)<<k for k,w in enumerate(wires))
        for b in range(len(m)):
            j=(i&~mask)|sum(((b>>k)&1)<<w for k,w in enumerate(wires))
            out[j,i]=m[b,a]
    return out

@pytest.mark.parametrize("wires",[(0,2),(2,0),(3,1),(1,3)])
@pytest.mark.parametrize("time",[-.37,0.,.81])
def test_local_observable_reuse(wires,time):
    H=q.Observable({"XX":.7,"YY":-.4,"ZZ":.2,"II":.9})
    expected=lift(dense_local(H),wires,4)
    embedded=embed(H,wires,width=4)
    assert embedded==prototype(H,wires,width=4)
    np.testing.assert_allclose(embedded.to_qiskit().to_matrix(),expected,atol=1e-9,rtol=0)
    old=q.Circuit(4).h(range(4)).apply(q.Circuit(2).evolve(H,time=time),wires=wires)
    candidate=local_evolution(q.Circuit(4).h(range(4)),H,time,wires=wires)
    np.testing.assert_allclose(Operator(old.to_qiskit()).data,Operator(candidate.to_qiskit()).data,atol=1e-9,rtol=0)
    rng=np.random.default_rng(1101);v=rng.normal(size=16)+1j*rng.normal(size=16);v/=np.linalg.norm(v)
    state=candidate.run(initial_state=v)
    raw=state.math.statevector()
    np.testing.assert_allclose(state.math.expectation(embedded),np.vdot(raw,expected@raw).real,atol=1e-9,rtol=0)

def test_symbolic_and_zero_width_semantics():
    H=q.Observable({"II":0.})
    assert embed(H,[2,0],width=4).to_dict()=={"IIII":0.}
    t=q.Circuit.parameter("t")
    H=q.Observable({"YX":.7,"II":.2})
    c=local_evolution(q.Circuit.symbolic(3),H,t,wires=[2,0])
    assert c.parameters==(t,)
    np.testing.assert_allclose(Operator(c.bind([.31]).to_qiskit()).data,expm(-.31j*lift(dense_local(H),[2,0],3)),atol=1e-9,rtol=0)

@pytest.mark.parametrize("wires",[[0],[0,0],[0,3],[0,1,2],{0,1},"01",[True,1]])
def test_invalid_remap_atomic(wires):
    H=q.Observable({"YX":.7});c=q.Circuit(3).h(0);before=c.to_qiskit()
    with pytest.raises(ValueError):local_evolution(c,H,.3,wires=wires)
    assert c.to_qiskit()==before


def test_bounded_embedding_and_immutability():
    H=q.Observable({"YX":.7,"II":.2});before=H.to_dict()
    seen=[]
    def infinite():
        i=0
        while True:
            seen.append(i);yield i;i+=1
    with pytest.raises(ValueError):H.on(infinite(),width=62)
    assert len(seen)==3 and H.to_dict()==before
    assert H.on([61,0],width=62).num_qubits==62
    with pytest.raises(q.ResourceLimit):H.on([0,1],width=63)
    with pytest.raises(ValueError):H.on([0,1],width=1)
    with pytest.raises(ValueError):H.on([0,1],width=True)
    embedded=H.on([3,1],width=4)
    exported=embedded.to_dict();exported.clear()
    assert H.to_dict()==before and embedded.to_dict()

def test_embedding_supports_composition_and_contract():
    H=q.Z(0)@q.Z(1)
    M=H.on([0,2],width=4)+H.on([1,3],width=4)
    c=q.Circuit(4).evolve(M,time=.31)
    assert c.contract(expectations={M:2.}).verify(c.run()).status=="PASS"
