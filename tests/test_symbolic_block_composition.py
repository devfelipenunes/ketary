"""Reusable symbolic blocks preserve native parameter identity and order."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator


def test_reusable_symbolic_layer_and_mapping():
    theta=q.Circuit.parameter("theta")
    phi=q.Circuit.parameter("phi")
    block=q.Circuit.symbolic(2).ry(theta,0).cx(0,1).rz(phi,1)
    original=block.to_qiskit()
    c=q.Circuit.symbolic(4).h(3)
    assert c.apply(block,wires=[3,0],times=2) is c
    c.apply_each(block,placements=[(1,2),(0,3)])
    assert set(c.parameters)=={theta,phi}
    native=QuantumCircuit(4)
    native.h(3)
    for a,b in [(3,0),(3,0),(1,2),(0,3)]:
        native.compose(original,qubits=[a,b],inplace=True)
    assert c.to_qiskit()==native and block.to_qiskit()==original
    for values in [(.3,-.8),(1.2,.7),(0.,0.)]:
        actual=c.bind(theta=values[0],phi=values[1]).to_qiskit()
        expected=native.assign_parameters(dict(zip((theta,phi),values)))
        np.testing.assert_allclose(Operator(actual).data,Operator(expected).data,atol=1e-12,rtol=0)


def test_symbolic_repeat_and_self_application():
    theta=q.Circuit.parameter("theta")
    block=q.Circuit.symbolic(2).rx(theta,0).cz(0,1)
    source=block.to_qiskit()
    repeat=block.repeat(3)
    assert repeat.parameters==(theta,)
    assert block.to_qiskit()==source
    assert repeat is not block
    block.apply(block,times=2)
    assert block.to_qiskit()==repeat.to_qiskit()
    assert len(block.to_qiskit().data)==6


def test_parameter_collision_rejected_before_mutation(monkeypatch):
    a=q.Circuit.parameter("theta")
    b=q.Circuit.parameter("theta")
    c=q.Circuit.symbolic(2).ry(a,0)
    block=q.Circuit.symbolic(1).rz(b,0)
    before=c.to_qiskit()
    def forbidden(*a,**kw):
        pytest.fail("native compose began before parameter preflight")
    monkeypatch.setattr(QuantumCircuit,"compose",forbidden)
    with pytest.raises(ValueError,match="conflicting parameter name"):
        c.apply(block,wires=[1])
    assert c.to_qiskit()==before and c.parameters==(a,)


def test_shared_parameter_and_bound_block():
    theta=q.Circuit.parameter("theta")
    c=q.Circuit.symbolic(2).ry(theta,0)
    c.apply(q.Circuit(2).cx(0,1))
    c.apply(q.Circuit.symbolic(1).rz(theta,0),wires=[1])
    assert c.parameters==(theta,)
    expected=q.Circuit(2).ry(.3,0).cx(0,1).rz(.3,1)
    c.bind(theta=.3).test.equivalent(expected).require()


def test_bound_only_operations_still_require_binding():
    theta=q.Circuit.parameter("theta")
    block=q.Circuit.symbolic(1).ry(theta,0)
    with pytest.raises(q.UnsupportedOperation):
        q.Circuit(2).apply(block,wires=[0])
    with pytest.raises(q.UnsupportedOperation):
        q.Circuit(2).apply_each(block,placements=[(0,),(1,)])
    with pytest.raises(q.UnsupportedOperation):
        q.Circuit.symbolic(2).apply(q.Circuit.classical(2,2))
    with pytest.raises(q.UnsupportedOperation):
        block.run()
    with pytest.raises(q.UnsupportedOperation):
        block.to_json()
    with pytest.raises(q.UnsupportedOperation):
        block.compose(block)


def test_symbolic_preflight_and_rollback(monkeypatch):
    theta=q.Circuit.parameter("theta")
    c=q.Circuit.symbolic(3).h(0).checkpoint("prefix")
    block=q.Circuit.symbolic(1).ry(theta,0)
    before=c.to_qiskit()
    original=QuantumCircuit.compose
    calls=[]
    def fail(self,*args,**kwargs):
        calls.append(1)
        result=original(self,*args,**kwargs)
        if len(calls)==2:
            self.global_phase=.7
            raise RuntimeError("injected")
        return result
    monkeypatch.setattr(QuantumCircuit,"compose",fail)
    for bad in [[(0,),(4,)],[(0,),None],[]]:
        with pytest.raises(ValueError):
            c.apply_each(block,placements=bad)
    with pytest.raises(q.ResourceLimit):
        c.apply_each(block,placements=itertools.repeat((0,)))
    assert calls==[]
    with pytest.raises(RuntimeError):
        c.apply_each(block,placements=[(0,),(2,)])
    assert c.to_qiskit()==before and c.parameters==()
    assert c.checkpoints=={"prefix":1}


def test_symbolic_sweep_after_composition():
    theta=q.Circuit.parameter("theta")
    block=q.Circuit.symbolic(1).ry(theta,0)
    c=q.Circuit.symbolic(2).apply_each(block,placements=[(0,),(1,)])
    results=c.sweep(theta=[0.,np.pi]).run()
    assert results[0].math.probability("00")==pytest.approx(1.)
    assert results[1].math.probability("11")==pytest.approx(1.)
