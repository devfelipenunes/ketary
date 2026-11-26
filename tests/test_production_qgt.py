"""Independent pure-state QGT formulas, gauge and rank cases."""
import numpy as np
import pytest
import ketary as q
from scipy.linalg import expm

@pytest.mark.parametrize("theta",[-2.4,-.8,0.,.2,1.1,2.7])
@pytest.mark.parametrize("phi",[-1.3,.4,2.1])
def test_qgt_bloch(theta,phi):
    a,b=q.Circuit.parameter_vector("v",2)
    c=q.Circuit.symbolic(1).ry(a,0).rz(b,0)
    before=c.to_qiskit()
    got=np.array(c.quantum_geometric_tensor({a:theta,b:phi}))
    s=np.sin(theta)
    want=np.array([[1,1j*s],[-1j*s,s*s]],complex)/4
    np.testing.assert_allclose(got,want,atol=1e-9,rtol=0)
    assert c.to_qiskit()==before
    assert np.linalg.eigvalsh(got).min()>=-1e-9

@pytest.mark.parametrize("seed",range(12))
def test_qgt_controlled_shared_and_phase(seed):
    rng=np.random.default_rng(seed+900)
    a,b=q.Circuit.parameter_vector("v",2)
    x,y=rng.uniform(-1,1,size=2)
    c=q.Circuit.symbolic(2).h([0,1]).crx(a*b,0,1).p(a,1).crx(b,0,1)
    # Independent dense generators and chain rule, including order.
    G=np.zeros((4,4),complex);G[1,3]=G[3,1]=.5
    P=np.diag([0,0,1,1])
    v=np.ones(4,complex)/2
    A=expm(-1j*x*y*G);B=expm(1j*x*P);C=expm(-1j*y*G)
    psi=C@B@A@v
    dx=C@(1j*P@B@A@v+B@(-1j*y*G@A)@v)
    dy=(-1j*G@C)@B@A@v+C@B@(-1j*x*G@A)@v
    D=np.column_stack([dx,dy])
    want=D.conj().T@(np.eye(4)-np.outer(psi,psi.conj()))@D
    got=np.array(c.quantum_geometric_tensor({a:x,b:y}))
    np.testing.assert_allclose(got,want,atol=1e-9,rtol=0)
    gauged=c.copy().evolve(q.I(),time=2*a-b)
    np.testing.assert_allclose(gauged.quantum_geometric_tensor({a:x,b:y}),want,atol=1e-9,rtol=0)

def test_qgt_rank_and_phase_only():
    a,b=q.Circuit.parameter_vector("v",2)
    c=q.Circuit.symbolic(1).ry(a+b,0)
    got=np.array(c.quantum_geometric_tensor({a:.1,b:.2}))
    np.testing.assert_allclose(got,np.ones((2,2))/4,atol=1e-9)
    assert np.linalg.matrix_rank(got,tol=1e-9)==1
    c=q.Circuit.symbolic(1).h(0).evolve(q.I(),time=a)
    np.testing.assert_allclose(c.quantum_geometric_tensor({a:.2}),[[0]],atol=1e-9)
    assert q.Circuit(1).quantum_geometric_tensor({})==()

def test_qgt_preflight_no_execution(monkeypatch):
    t=q.Circuit.parameter("t")
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("unexpected simulation"))
    c=q.Circuit.symbolic(1).ry(t,0)
    for b in ({},{t:float("nan")},{q.Circuit.parameter("t"):.1}):
        with pytest.raises(ValueError):c.quantum_geometric_tensor(b)
    with pytest.raises(q.ResourceLimit):c.quantum_geometric_tensor({t:.1},max_bytes=1)
    with pytest.raises(q.UnsupportedOperation):q.Circuit.symbolic(1).u(t,.2,.3,0).quantum_geometric_tensor({t:.1})
    for _ in range(32):c.ry(t,0)
    with pytest.raises(q.ResourceLimit):c.quantum_geometric_tensor({t:.1})
    with pytest.raises(q.UnsupportedOperation):q.Circuit.classical(1,1).quantum_geometric_tensor({})
