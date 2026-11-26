"""Independent analytic controlled-rotation derivative oracle."""
import numpy as np
import pytest
import ketary as q

@pytest.mark.parametrize("axis",["x","y","z"])
@pytest.mark.parametrize("seed",range(12))
def test_controlled_derivative(axis,seed):
    rng=np.random.default_rng(seed+1201)
    P={"x":np.array([[0,1],[1,0]]),"y":np.array([[0,-1j],[1j,0]]),"z":np.diag([1,-1])}[axis]
    G=np.zeros((4,4),complex)
    G[np.ix_([1,3],[1,3])]=P/2
    a,b=q.Circuit.parameter_vector("v",2)
    x,y=rng.uniform(-1,1,size=2)
    c=q.Circuit.symbolic(2).h([0,1]).ry(.31,0).rz(.4,1)
    # Independent prefix via explicit Kronecker products; avoid using the SDK as oracle.
    h=np.array([[1,1],[1,-1]])/np.sqrt(2)
    ry=np.array([[np.cos(.31/2),-np.sin(.31/2)],[np.sin(.31/2),np.cos(.31/2)]])
    rz=np.diag(np.exp(1j*np.array([-.2,.2])))
    initial=np.kron(rz@h,ry@h)[:,0]
    getattr(c,"cr"+axis)(a*b,0,1)
    getattr(c,"cr"+axis)(2*a-b,0,1)
    theta=x*y+2*x-y
    from scipy.linalg import expm
    psi=expm(-1j*theta*G)@initial
    X=np.array([[0,1],[1,0]])
    Y=np.array([[0,-1j],[1j,0]])
    Z=np.diag([1,-1])
    matrices=[np.kron(X,np.eye(2)),np.kron(np.eye(2),Y),np.kron(Z,Z)]
    # d< O >/dtheta = i < [G,O] >; includes both frequency gaps.
    wanted=np.array([float((1j*np.vdot(psi,(G@M-M@G)@psi)).real) for M in matrices])[:,None]*np.array([y+2,x-1])
    before=c.to_qiskit()
    np.testing.assert_allclose(c.expectation_jacobian({a:x,b:y},[q.X(1),q.Y(0),q.Z(0)@q.Z(1)]),wanted,atol=1e-9,rtol=0)
    assert c.to_qiskit()==before

def test_controlled_shift_budget_before_any_run(monkeypatch):
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(2).h(0)
    for _ in range(33):c.crx(t,0,1)
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("shift budget must precede execution"))
    with pytest.raises(q.ResourceLimit,match="128"):c.expectation_jacobian({t:.3},[q.Z(1)])
    c=q.Circuit.symbolic(2)
    for _ in range(31):c.cry(t,0,1)
    for _ in range(3):c.ry(t,0)
    with pytest.raises(q.ResourceLimit,match="128"):c.expectation_jacobian({t:.3},[q.Z(1)])

def test_both_controlled_frequencies():
    # Control coherence yields cos(theta/2), target expectation yields cos(theta).
    t=q.Circuit.parameter("t");c=q.Circuit.symbolic(2).h(0).crx(t,0,1)
    for v in (.2,.7,-1.3):
        np.testing.assert_allclose(c.expectation_jacobian({t:v},[q.X(0),q.Z(1)]),[[-.5*np.sin(v/2)],[-.5*np.sin(v)]],atol=1e-9,rtol=0)
