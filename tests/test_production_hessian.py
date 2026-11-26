"""Independent second-order analytic expectation references."""
import numpy as np
import pytest
import ketary as q

@pytest.mark.parametrize("theta",[-1.2,0.,.2,1.4])
@pytest.mark.parametrize("phi",[-.8,.0,.7])
def test_hessian_bloch(theta,phi):
    a,b=q.Circuit.parameter_vector("v",2)
    c=q.Circuit.symbolic(1).ry(a,0).rz(b,0)
    before=c.to_qiskit()
    s,t=np.sin(theta),np.cos(theta)
    u,v=np.sin(phi),np.cos(phi)
    expected=[[[-s*v,-t*u],[-t*u,-s*v]],[[-s*u,t*v],[t*v,-s*u]],[[-t,0],[0,0]]]
    got=c.expectation_hessian({a:theta,b:phi},[q.X(0),q.Y(0),q.Z(0)])
    np.testing.assert_allclose(got,expected,atol=1e-9,rtol=0)
    assert c.to_qiskit()==before

@pytest.mark.parametrize("a0,b0",[(0.,0.),(.2,.8),(-.7,.3),(.4,-1.1)])
def test_nonlinear_shared_hessian(a0,b0):
    a,b=q.Circuit.parameter_vector("v",2)
    c=q.Circuit.symbolic(1).ry(a*a,0).ry(a*b,0)
    theta=a0*a0+a0*b0
    g=np.array([2*a0+b0,a0]);H=np.array([[2.,1.],[1.,0.]])
    expected=-np.cos(theta)*np.outer(g,g)-np.sin(theta)*H
    # X expectation has nonzero second derivative even at zero gradient.
    expected_x=-np.sin(theta)*np.outer(g,g)+np.cos(theta)*H
    np.testing.assert_allclose(c.expectation_hessian({a:a0,b:b0},[q.Z(0),q.X(0)]),[expected,expected_x],atol=1e-9,rtol=0)

@pytest.mark.parametrize("theta",[-1.1,.0,.3,1.9])
def test_controlled_second_frequency(theta):
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(2).h(0).crx(t,0,1)
    np.testing.assert_allclose(c.expectation_hessian({t:theta},[q.X(0),q.Z(1)]),[[[-.25*np.cos(theta/2)]],[[-.5*np.cos(theta)]]],atol=1e-9,rtol=0)

def test_mixed_controlled_and_regular_chain():
    a,b=q.Circuit.parameter_vector("v",2)
    c=q.Circuit.symbolic(2).h(0).crx(a*b,0,1).rx(b,1)
    x,y=.37,-.62
    # Z target = (cos(b)+cos(a*b+b))/2.
    v=x*y+y;g=np.array([y,x+1]);H=np.array([[0.,1.],[1.,0.]])
    expected=(-np.cos(v)*np.outer(g,g)-np.sin(v)*H)/2
    expected[1,1]-=np.cos(y)/2
    np.testing.assert_allclose(c.expectation_hessian({a:x,b:y},[q.Z(1)])[0],expected,atol=1e-9,rtol=0)

def test_hessian_phase_and_empty():
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(1).h(0).evolve(q.I(),time=t*t)
    assert c.expectation_hessian({t:.2},[q.X(0)])==(((0.,),),)
    assert q.Circuit(1).expectation_hessian({},[q.Z(0)])==((),)

def test_hessian_invalid_preflight(monkeypatch):
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(1).ry(t,0)
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("unexpected simulation"))
    with pytest.raises(ValueError):c.expectation_hessian({},[q.Z(0)])
    with pytest.raises(ValueError):c.expectation_hessian({t:.3},[q.Z(1)])
    with pytest.raises(q.ResourceLimit):c.expectation_hessian({t:.3},[q.Z(0)],max_bytes=1)
    with pytest.raises(q.UnsupportedOperation):q.Circuit.symbolic(1).u(t,.2,.3,0).expectation_hessian({t:.3},[q.Z(0)])
    for _ in range(8):c.ry(t,0)
    with pytest.raises(q.ResourceLimit):c.expectation_hessian({t:.3},[q.Z(0)])
    c=q.Circuit.symbolic(2)
    for _ in range(8):c.crx(t,0,1)
    with pytest.raises(q.ResourceLimit,match="256"):c.expectation_hessian({t:.3},[q.Z(0)])
