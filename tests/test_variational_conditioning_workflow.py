"""Analytic coupled derivative and near-null-direction integration oracles."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit import ParameterVector

@pytest.mark.parametrize("eps",[0.,1e-8,1e-5,.2])
@pytest.mark.parametrize("x,y",[(0.,0.),(.37,-.62),(-1.2,.9)])
def test_expressive_variational_chain(eps,x,y):
    a,b=q.Circuit.parameter_vector("p",2)
    # One reusable symbolic block, disjoint placements, shared parameters.
    layer=q.Circuit.symbolic(1).ry(a+b,0)
    c=q.Circuit.symbolic(3).apply_each(layer,placements=[(0,),(2,)])
    c.ry(eps*b,1).evolve(q.I(2),time=a*a+b)
    before=c.to_qiskit()
    bindings={a:x,b:y}
    angle=x+y
    # Product state plus global phase, computed directly without Qiskit.
    rot=lambda t:np.array([np.cos(t/2),np.sin(t/2)],complex)
    psi=np.exp(-1j*(x*x+y))*np.kron(np.kron(rot(angle),rot(eps*y)),rot(angle))
    r=c.bind(bindings).run()
    np.testing.assert_allclose(r.math.statevector(),psi,atol=1e-9,rtol=0)
    # Matched native circuit, including global phase and absolute wire order.
    p=ParameterVector("p",2)
    native=QuantumCircuit(3)
    native.ry(p[0]+p[1],0);native.ry(p[0]+p[1],2)
    native.ry(eps*p[1],1);native.global_phase=-(p[0]*p[0]+p[1])
    native=native.assign_parameters({p[0]:x,p[1]:y})
    np.testing.assert_allclose(Operator(c.bind(bindings).to_qiskit()).data,
                               Operator(native).data,atol=1e-9,rtol=0)
    # H=(Z0+Z2)/2 and Z1. Closed form: cos(x+y), cos(eps*y).
    H=(q.Z(0)+q.Z(2))*.5
    K=q.Z(1)
    obs=[H,K]
    E=np.array([np.cos(angle),np.cos(eps*y)])
    J=np.array([[-np.sin(angle),-np.sin(angle)],[0.,-eps*np.sin(eps*y)]])
    Hess=np.array([-np.cos(angle)*np.ones((2,2)),
                  [[0.,0.],[0.,-eps**2*np.cos(eps*y)]]])
    G=np.ones((2,2))/2
    G[1,1]+=eps**2/4
    np.testing.assert_allclose(r.math.expectations(obs),E,atol=1e-9,rtol=0)
    np.testing.assert_allclose(c.expectation_jacobian(bindings,obs),J,atol=1e-9,rtol=0)
    np.testing.assert_allclose(c.expectation_hessian(bindings,obs),Hess,atol=1e-9,rtol=0)
    got=np.array(c.quantum_geometric_tensor(bindings))
    np.testing.assert_allclose(got,G,atol=1e-9,rtol=0)
    np.testing.assert_allclose(got,got.conj().T,atol=1e-12,rtol=0)
    assert np.linalg.eigvalsh(got).min()>=-1e-9
    # Do not assert a numerical rank for eps=1e-8; smaller than resolution.
    if eps==0:
        np.testing.assert_allclose(got@np.array([1.,-1.]),0.,atol=1e-9,rtol=0)
    elif eps==.2:
        assert np.linalg.eigvalsh(got).min()>0
    contract=c.bind(bindings).contract(expectations={H:float(E[0]),K:float(E[1])})
    contract.verify(r).require()
    assert c.to_qiskit()==before
    assert layer.parameters==(a,b)

@pytest.mark.parametrize("method",["expectation_jacobian","expectation_hessian","quantum_geometric_tensor"])
def test_shared_parameter_wrong_identity_preflight(method,monkeypatch):
    a,b=q.Circuit.parameter_vector("p",2)
    layer=q.Circuit.symbolic(1).ry(a+b,0)
    c=q.Circuit.symbolic(3).apply_each(layer,placements=[(0,),(2,)])
    other=q.Circuit.parameter("p[0]")
    monkeypatch.setattr(q.Circuit,"run",lambda *args,**kwargs:pytest.fail("invalid parameter executed"))
    call=getattr(c,method)
    args=({other:.2,b:.3},) if method=="quantum_geometric_tensor" else ({other:.2,b:.3},[q.Z(0)])
    with pytest.raises(ValueError):call(*args)
