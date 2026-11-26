import numpy as np
import pytest
import ketary as q
from research.occurrence_gradient import jacobian

@pytest.mark.parametrize("value",[.17,.37,-.81])
def test_shared_parameter_and_chain_rule(value):
    t=q.Circuit.parameter("t");c=q.Circuit.symbolic(1).ry(t,0).ry(2*t,0)
    raw=c.to_qiskit()
    g=jacobian(c,{t:value},[q.Z(0),q.X(0)])
    np.testing.assert_allclose(g["jacobian"][:,0],[-3*np.sin(3*value),3*np.cos(3*value)],atol=1e-9,rtol=0)
    assert g["simulation_count"]==4 and c.to_qiskit()==raw

@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_jacobian_multiple_parameters_and_symbolic_hamiltonian(seed):
    a,b=q.Circuit.parameter_vector("p",2)
    c=q.Circuit.symbolic(2).h([0,1]).evolve(q.I()+q.Y(0)@q.X(1),time=a*b).ry(a,0).rzz(b,0,1)
    values=dict(zip((a,b),np.random.default_rng(seed).uniform(-.6,.6,2),strict=True))
    obs=[q.Z(0),q.X(0)@q.Y(1),q.Z(0)@q.Z(1)]
    got=jacobian(c,values,obs)
    expected=[]
    for p in got["parameters"]:
        plus=dict(values);minus=dict(values);plus[p]+=1e-5;minus[p]-=1e-5
        r=c.bind(plus).run();s=c.bind(minus).run()
        expected.append([(r.math.expectation(H)-s.math.expectation(H))/2e-5 for H in obs])
    np.testing.assert_allclose(got["jacobian"],np.array(expected).T,atol=1e-8,rtol=0)

def test_phase_only_parameter_has_zero_expectation_derivative():
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(1).h(0).evolve(q.I(),time=t)
    out=jacobian(c,{t:.31},[q.X(0)])
    assert out["simulation_count"]==0
    np.testing.assert_array_equal(out["jacobian"],[[0.]])

def test_unsupported_and_bad_bindings_fail_before_execution(monkeypatch):
    t=q.Circuit.parameter("t");c=q.Circuit.symbolic(2).crx(t,0,1)
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("simulation before preflight"))
    with pytest.raises(q.UnsupportedOperation):jacobian(c,{t:.3},[q.Z(0)])
    with pytest.raises(ValueError):jacobian(c,{q.Circuit.parameter("t"):.3},[q.Z(0)])
    with pytest.raises(ValueError):jacobian(c,{t:float("nan")},[q.Z(0)])
    with pytest.raises(ValueError):jacobian(c,{t:.3},[q.Z(2)])

@pytest.mark.parametrize("gate",["rx","ry","rz","rxx","ryy","rzz","p","cp"])
def test_supported_gate_generators(gate):
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(2).h([0,1]).ry(.27,0)
    getattr(c,gate)(t,0,1) if gate in ("rxx","ryy","rzz","cp") else getattr(c,gate)(t,0)
    H=q.X(0)+.7*q.Y(1)+.2*q.Z(0)@q.Z(1)
    f=lambda x:c.bind({t:x}).run().math.expectation(H)
    g=jacobian(c,{t:.37},[H])
    assert g["jacobian"][0,0]==pytest.approx((f(.37001)-f(.36999))/2e-5,abs=1e-8)
