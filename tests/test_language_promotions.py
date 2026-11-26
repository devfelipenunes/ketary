"""LANG03 and LANG05 candidate runtime contracts."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

@pytest.mark.parametrize("label",["0","1","0000","1010","0101","1111"])
def test_basis_is_unitary_not_reset(label):
    raw=QuantumCircuit(len(label))
    for i,b in enumerate(reversed(label)):
        if b=="1":raw.x(i)
    c=q.basis(label)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(raw).data,atol=1e-9,rtol=0)
    c.run().test.probability(label,1).require()
    q.Circuit(len(label)+1).apply(c,wires=range(1,len(label)+1))

@pytest.mark.parametrize("label",["","02",None,101])
def test_basis_invalid(label):
    with pytest.raises(ValueError):q.basis(label)

def test_basis_cap():
    with pytest.raises(q.ResourceLimit):q.basis("0"*63)
    assert q.basis("0"*62).num_qubits==62

@pytest.mark.parametrize("value",[.17,.37,-.81])
def test_jacobian_shared_parameter(value):
    t=q.Circuit.parameter("t");c=q.Circuit.symbolic(1).ry(t,0).ry(2*t,0)
    raw=c.to_qiskit()
    actual=c.expectation_jacobian({t:value},[q.Z(0),q.X(0)])
    np.testing.assert_allclose(actual,[[-3*np.sin(3*value)],[3*np.cos(3*value)]],atol=1e-9,rtol=0)
    assert c.to_qiskit()==raw and type(actual) is tuple and type(actual[0]) is tuple

@pytest.mark.parametrize("gate",["rx","ry","rz","rxx","ryy","rzz","p","cp"])
def test_jacobian_supported_generator(gate):
    t=q.Circuit.parameter("t");c=q.Circuit.symbolic(2).h([0,1]).ry(.27,0)
    if gate in ("rxx","ryy","rzz","cp"):getattr(c,gate)(t,0,1)
    else:getattr(c,gate)(t,0)
    H=q.X(0)+.7*q.Y(1)+.2*q.Z(0)@q.Z(1)
    f=lambda x:c.bind({t:x}).run().math.expectation(H)
    assert c.expectation_jacobian({t:.37},[H])[0][0]==pytest.approx((f(.37001)-f(.36999))/2e-5,abs=1e-8)

def test_jacobian_phase_only_and_preflight(monkeypatch):
    t=q.Circuit.parameter("t");phase=q.Circuit.symbolic(1).h(0).evolve(q.I(),time=t)
    bad=q.Circuit.symbolic(2).u(t,.2,.3,0)
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("unexpected evolution"))
    assert phase.expectation_jacobian({t:.3},[q.X(0)])==((0.,),)
    with pytest.raises(q.UnsupportedOperation):bad.expectation_jacobian({t:.3},[q.Z(0)])
    with pytest.raises(ValueError):phase.expectation_jacobian({q.Circuit.parameter("t"):.3},[q.X(0)])
    with pytest.raises(ValueError):phase.expectation_jacobian({t:float("nan")},[q.X(0)])
    with pytest.raises(ValueError):phase.expectation_jacobian({t:.3},[q.X(1)])
    with pytest.raises(q.ResourceLimit):phase.expectation_jacobian({t:.3},[q.X(0)],max_bytes=95)

def test_jacobian_multiple_parameters_and_symbolic_hamiltonian():
    a,b=q.Circuit.parameter_vector("p",2)
    c=q.Circuit.symbolic(2).h([0,1]).evolve(q.I()+q.Y(0)@q.X(1),time=a*b).ry(a,0).rzz(b,0,1)
    values={a:.2,b:-.4};obs=[q.Z(0),q.X(0)@q.Y(1),q.Z(0)@q.Z(1)]
    want=[]
    for p in c.parameters:
        plus=dict(values);minus=dict(values);plus[p]+=1e-5;minus[p]-=1e-5
        want.append((np.asarray(c.bind(plus).run().math.expectations(obs))-np.asarray(c.bind(minus).run().math.expectations(obs)))/2e-5)
    np.testing.assert_allclose(c.expectation_jacobian(values,obs),np.array(want).T,atol=1e-8,rtol=0)
