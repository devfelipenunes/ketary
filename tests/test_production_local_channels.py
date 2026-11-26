"""Independent local and composed quantum channel oracles."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Kraus,DensityMatrix

def embed(K,n,wires):
    out=np.zeros((1<<n,1<<n),complex)
    mask=sum(1<<w for w in wires)
    for source in range(1<<n):
        local=sum(((source>>w)&1)<<i for i,w in enumerate(wires))
        for dest in range(1<<len(wires)):
            target=(source&~mask)|sum(((dest>>i)&1)<<w for i,w in enumerate(wires))
            out[target,source]=K[dest,local]
    return out

def amplitude(g):
    return [np.diag([1.,np.sqrt(1-g)]),np.array([[0,np.sqrt(g)],[0,0]])]

@pytest.mark.parametrize("n,wires",[(2,[0]),(2,[1]),(3,[2]),(4,[1]),(5,[4]),(3,[2,0]),(3,[0,2]),(4,[3,1])])
@pytest.mark.parametrize("seed",range(4))
def test_local_channel_dense_oracle(n,wires,seed):
    rng=np.random.default_rng(seed+177)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    v/=np.linalg.norm(v)
    rho=np.outer(v,v.conj())
    ks=amplitude(.31)
    if len(wires)==2:
        ks=[np.kron(np.array([[0,1],[1,0]]),K) for K in ks]
    matrices=[embed(K,n,wires) for K in ks]
    expected=sum(K@rho@K.conj().T for K in matrices)
    initial=DensityMatrix(rho)
    got=q.Circuit(n).run_channel(Kraus(ks),initial,wires=wires)
    np.testing.assert_allclose(got.data,expected,atol=1e-9,rtol=0)
    np.testing.assert_array_equal(initial.data,rho)
    assert got.num_qubits==n and got.is_valid()

@pytest.mark.parametrize("g,p",[(0.,0.),(.1,.3),(.9,.7),(1.,1.)])
def test_composed_channel_oracle(g,p):
    A=amplitude(g);B=[np.sqrt(1-p)*np.eye(2),np.sqrt(p)*np.diag([1,-1])]
    composed=Kraus(A).compose(Kraus(B))
    c=q.bell()
    rho=c.run_density().data
    E=[embed(b@a,2,[1]) for a,b in itertools.product(A,B)]
    expected=sum(K@rho@K.conj().T for K in E)
    np.testing.assert_allclose(c.run_channel(composed,wires=[1]).data,expected,atol=1e-9,rtol=0)

def test_local_channel_budget_and_invalid_before_execution(monkeypatch):
    c=q.Circuit(5)
    monkeypatch.setattr(DensityMatrix,"from_instruction",lambda *a,**kw:pytest.fail("execution before preflight"))
    channel=Kraus(amplitude(.2))
    for wires in ([],[0,0],[5],[-1],[True],{1},[0,1]):
        with pytest.raises(ValueError):c.run_channel(channel,wires=wires)
    with pytest.raises(q.ResourceLimit):c.run_channel(channel,wires=itertools.count())
    required=16*(3*4**5+2*4)
    with pytest.raises(q.ResourceLimit):c.run_channel(channel,wires=[4],max_bytes=required-1)

def test_full_width_explicit_order():
    c=q.bell()
    K=Kraus([np.kron(np.eye(2),a) for a in amplitude(.2)])
    np.testing.assert_allclose(c.run_channel(K).data,c.run_channel(K,wires=[0,1]).data,atol=1e-9)
