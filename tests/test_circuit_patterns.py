"""Ordered topology and aligned rotation contracts, checked against Qiskit."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

def test_topology_order_and_bounds():
    wires=[3,0,2,1]
    assert q.chain(iter(wires))==((3,0),(0,2),(2,1))
    assert q.ring(wires)==((3,0),(0,2),(2,1),(1,3))
    assert q.star(wires)==((3,0),(3,2),(3,1))
    assert q.all_pairs(wires)==((3,0),(3,2),(3,1),(0,2),(0,1),(2,1))
    assert q.Circuit(4).wires==range(4)
    for fn in (q.chain,q.ring,q.star,q.all_pairs):
        for bad in ([],[1],[0,0,1],[True,1,2],[-1,1,2],{0,1,2},"123"):
            with pytest.raises(ValueError):
                fn(bad)
    with pytest.raises(ValueError):
        q.ring([0,1])
    with pytest.raises(q.ResourceLimit):
        q.all_pairs(range(142))
    with pytest.raises(q.ResourceLimit):
        q.chain(range(4097))

@pytest.mark.parametrize("gate",["rx","ry","rz","p"])
def test_zipped_rotations(gate):
    c=q.Circuit(4).h(1).checkpoint("before")
    native=QuantumCircuit(4)
    native.h(1)
    wires=[3,0,2]
    angles=[.7,-.19,1.1]
    assert getattr(c,gate)(iter(angles),iter(wires)) is c
    for w,a in zip(wires,angles):
        getattr(native,gate)(a,w)
    assert c.to_qiskit()==native and c.checkpoints=={"before":1}
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(native).data,rtol=0,atol=1e-12)
    before=c.to_json()
    for a,w in (([1,2],[0]),([1],[0,1]),([1,float("nan")],[0,1]),([True,2],[0,1]),([1,2],[0,0]),([1,2],{0,1}),({1,2},[0,1]),([1],0)):
        with pytest.raises(ValueError):
            getattr(c,gate)(a,w)
        assert c.to_json()==before

def test_parameter_vectors_and_classical_rotations():
    a=q.Circuit.parameter("a")
    b=q.Circuit.parameter("b")
    c=q.Circuit.symbolic(2).ry([a,2*b],[1,0])
    bound=c.bind(a=.2,b=.3)
    expected=q.Circuit(2).ry(.2,1).ry(.6,0)
    bound.test.equivalent(expected).require()
    original=c.to_qiskit()
    same_name=q.Circuit.parameter("a")
    with pytest.raises(Exception):
        c.ry([same_name,b],[0,1])
    assert c.to_qiskit()==original
    d=q.Circuit.classical(2,2).rz([.2,.3],[0,1])
    native=QuantumCircuit(2,2)
    native.rz(.2,0)
    native.rz(.3,1)
    assert d.to_qiskit()==native
