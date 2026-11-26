"""Expressive pair grammar with exact sequence and failure atomicity."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

GATES=[("cx",()),("cz",()),("swap",()),("ch",()),("cy",()),
       ("cp",(.2,)),("crx",(.3,)),("cry",(-.2,)),("crz",(.4,)),
       ("rxx",(.5,)),("ryy",(.6,)),("rzz",(.7,))]


@pytest.mark.parametrize("name,params",GATES)
def test_pair_sequence_matches_scalar_and_strict_operator(name,params):
    native=QuantumCircuit(4,global_phase=.23)
    native.h(0)
    c=q.from_qiskit(native).checkpoint("ready")
    pairs=[(3,0),(0,1),(1,3),(3,0),(2,1)]
    for a,b in pairs:
        getattr(native,name)(*params,a,b)
    assert getattr(c,name)(*params,pairs=(iter(p) for p in pairs)) is c
    assert c.to_qiskit()==native
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(native).data,atol=1e-12,rtol=0)
    assert c.checkpoints=={"ready":1}


@pytest.mark.parametrize("pairs",[[],[(0,0)],[(0,1),(1,4)],[(True,1)],
    [(0,1,2)],[(0,)],{(0,1)},[{0,1}],{0:1},"01",[0],[(0,1),(0,1.5)]])
def test_invalid_pairs_preflight(pairs,monkeypatch):
    c=q.Circuit(4).h(0)
    before=c.to_json()
    def forbidden(*a,**kw):
        pytest.fail("native mutation before preflight")
    monkeypatch.setattr(QuantumCircuit,"cx",forbidden)
    with pytest.raises(ValueError):
        c.cx(pairs=pairs)
    assert c.to_json()==before


def test_pair_limit_and_mixed_arguments(monkeypatch):
    c=q.Circuit(2).h(0)
    before=c.to_json()
    def forbidden(*a,**kw):
        pytest.fail("native mutation before preflight")
    monkeypatch.setattr(QuantumCircuit,"cx",forbidden)
    with pytest.raises(q.ResourceLimit):
        c.cx(pairs=itertools.repeat((0,1)))
    for args in ((0,1),(0,)):
        with pytest.raises(ValueError):
            c.cx(*args,pairs=[(0,1)])
    assert c.to_json()==before


def test_late_native_failure_rolls_back(monkeypatch):
    native=QuantumCircuit(3,global_phase=.2)
    native.h(0)
    c=q.from_qiskit(native).checkpoint("prefix")
    before=c.to_json()
    original=QuantumCircuit.cz
    def fail(self,*a,**kw):
        original(self,2,0)
        self.global_phase=.8
        raise RuntimeError("injected")
    monkeypatch.setattr(QuantumCircuit,"cz",fail)
    with pytest.raises(RuntimeError):
        c.cz(pairs=q.ring(c.wires))
    assert c.to_json()==before and c.checkpoints=={"prefix":1}


def test_symbolic_and_dynamic_modes_remain_explicit():
    theta=q.Circuit.parameter("theta")
    c=q.Circuit.symbolic(3).rzz(theta,pairs=q.chain(range(3)))
    assert c.parameters==(theta,)
    native=QuantumCircuit(3)
    native.rzz(.3,0,1)
    native.rzz(.3,1,2)
    assert c.bind(theta=.3).to_qiskit()==native
    dynamic=q.Circuit.classical(3,3).h(0).cx(pairs=q.chain(range(3))).measure(range(3),range(3))
    expected=QuantumCircuit(3,3)
    expected.h(0)
    expected.cx(0,1)
    expected.cx(1,2)
    expected.measure(range(3),range(3))
    assert dynamic.to_qiskit()==expected


def test_explicit_topologies_and_large_pair_sequence():
    n=32
    c=q.Circuit(n).cz(pairs=q.ring(range(n)))
    native=QuantumCircuit(n)
    for a,b in q.ring(range(n)):
        native.cz(a,b)
    assert c.to_qiskit()==native
    c=q.Circuit(2).cx(pairs=itertools.repeat((0,1),10000))
    assert len(c.to_qiskit().data)==10000
