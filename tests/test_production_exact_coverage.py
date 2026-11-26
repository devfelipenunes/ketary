"""Meaningful preflight and resource failure coverage before an exact CI gate."""
import math
import numpy as np
import pytest
import ketary as q

def test_named_annotations_limits():
    c=q.Circuit(1)
    for name in ["bad name","a"*65,object()]:
        with pytest.raises(ValueError):c.register(name,[0])
    for i in range(32):
        c.register(f"r{i}",[0]);c.checkpoint(f"p{i}")
    with pytest.raises(q.ResourceLimit):c.register("overflow",[0])
    with pytest.raises(q.ResourceLimit):c.checkpoint("overflow")
    with pytest.raises(ValueError):c.checkpoint("p0")
    assert len(c.registers)==len(c.checkpoints)==32

def test_invalid_ordered_operations():
    c=q.Circuit(2);before=c.to_qiskit()
    for fn in (lambda:c.apply_each(q.bell(),placements=1),lambda:c.run_many(1),lambda:c.ccx(0,0,1)):
        with pytest.raises(ValueError):fn()
    for fn in (lambda:c.apply(object()),lambda:c.compose(object())):
        with pytest.raises(TypeError):fn()
    assert c.to_qiskit()==before

def test_binding_and_sweep_contracts():
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(1).ry(t,0)
    with pytest.raises(ValueError):c.bind(wrong=.2)
    with pytest.raises(TypeError):c.bind(1)
    with pytest.raises(TypeError):q.SweepPlan(object(),{})
    for fn in (lambda:c.sweep(wrong=[.2]),lambda:c.sweep(t={.2}),lambda:c.sweep_rows(["bad"]),lambda:c.sweep_rows([1]),lambda:q.Circuit(1).sweep_rows([[.2]])):
        with pytest.raises(ValueError):fn()
    classical=q.Circuit.classical(1,1)
    with pytest.raises(q.UnsupportedOperation):classical.sweep(t=[.2])
    with pytest.raises(q.UnsupportedOperation):classical.sweep_rows([[.2]])
    wide=q.Circuit.symbolic(13).ry(t,0)
    with pytest.raises(q.ResourceLimit):wide.sweep(t=[.2])
    with pytest.raises(q.ResourceLimit):wide.sweep_rows([[.2]])

@pytest.mark.parametrize("method",["expectation_jacobian","expectation_hessian"])
def test_differential_preflight(method,monkeypatch):
    t=q.Circuit.parameter("t");c=q.Circuit.symbolic(1).ry(t,0)
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**kw:pytest.fail("execution during invalid preflight"))
    for obs in ("Z",1,{q.Z(0)},{}):
        with pytest.raises(ValueError):getattr(c,method)({t:.3},obs)
    for obs in ([],[q.Z(0)]*9):
        with pytest.raises(q.ResourceLimit):getattr(c,method)({t:.3},obs)
    with pytest.raises(q.ResourceLimit):getattr(q.Circuit.symbolic(9).ry(t,0),method)({t:.3},[q.Z(0)])
    with pytest.raises(q.UnsupportedOperation):getattr(q.Circuit.classical(1,1),method)({},[q.Z(0)])

def test_qgt_nonfinite_and_width():
    t=q.Circuit.parameter("t")
    with pytest.raises(q.ResourceLimit):q.Circuit.symbolic(9).ry(t,0).quantum_geometric_tensor({t:.2})
    c=q.Circuit.symbolic(1).ry(1e200*t,0)
    with pytest.raises(ArithmeticError):c.quantum_geometric_tensor({t:0.})

def test_differential_fixed_and_stationary_angles():
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(1).ry(.3,0).ry(t*t,0).ry(t,0)
    got=c.expectation_hessian({t:0.},[q.X(0),q.Z(0)])
    np.testing.assert_allclose(got,[[[2*np.cos(.3)-np.sin(.3)]],[[-2*np.sin(.3)-np.cos(.3)]]],atol=1e-9)
    np.testing.assert_allclose(c.quantum_geometric_tensor({t:0.}),[[.25]],atol=1e-9)
    # All angle derivatives vanish at zero for a cubic expression.
    d=q.Circuit.symbolic(1).ry(t*t*t,0)
    assert d.expectation_hessian({t:0.},[q.Z(0)])==(((0.,),),)

def test_decoder_invalid_inputs():
    for fn in (lambda:q.decode_phase_estimation(q.Circuit(1).run(),precision=13),lambda:q.decode_bernstein_vazirani(q.Circuit(1).run())):
        with pytest.raises(q.ResourceLimit):fn()
    for fn in (lambda:q.decode_phase_estimation(object(),precision=1),lambda:q.decode_teleportation(object())):
        with pytest.raises(TypeError):fn()
    bad=q.ShotResult(8,3,0,(("000",7),),((1,2,2),))
    with pytest.raises(ValueError):q.decode_teleportation(bad)

def test_algorithm_preflight():
    with pytest.raises(ValueError):q.ansatz(2,rotations=1)
    with pytest.raises(q.ResourceLimit):q.maxcut_hamiltonian(63,[(0,1)])
    for edges in ([{0,1}],1):
        with pytest.raises(ValueError):q.maxcut_hamiltonian(2,edges)
    for weights in ({1.},1):
        with pytest.raises(ValueError):q.maxcut_hamiltonian(2,[(0,1)],weights=weights)
    with pytest.raises(ValueError):q.phase_oracle(1)
    with pytest.raises(TypeError):q.amplitude_amplification(object(),iterations=1)
    block=q.Circuit(2)
    for _ in range(1600):block.h(0)
    with pytest.raises(q.ResourceLimit):q.amplitude_amplification(block,iterations=64)

def test_commuting_zero_angle_no_gate():
    c=q.Circuit(2);before=c.to_qiskit()
    c.evolve(q.X(0)@q.X(1),time=0.)
    assert c.to_qiskit()==before

def test_channel_wire_noniterable():
    from qiskit.quantum_info import Kraus
    with pytest.raises(ValueError):q.Circuit(1).run_channel(Kraus([np.eye(2)]),wires=1)
