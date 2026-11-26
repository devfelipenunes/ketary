"""Bounded batch ingestion retains native order, validation and rollback."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

@pytest.mark.parametrize("gate",["cx","cz","swap","rzz","cp"])
@pytest.mark.parametrize("kind",["tuple","list","iterator"])
def test_ordered_pair_ingestion(gate,kind):
    rows=[(3,0),(2,1),(0,2),(3,0)]
    inputs=[tuple(r) if kind=="tuple" else list(r) if kind=="list" else iter(r) for r in rows]
    c=q.Circuit(4).h(range(4))
    native=QuantumCircuit(4);native.h(range(4))
    args=(.37,) if gate in ("rzz","cp") else ()
    for row in rows:getattr(native,gate)(*args,*row)
    getattr(c,gate)(*args,pairs=iter(inputs))
    assert c.to_qiskit()==native
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(native).data,atol=1e-9,rtol=0)

@pytest.mark.parametrize("bad",[(0,), (0,1,2), (True,1),(0,0),(-1,1),(0,4),{"a":0,"b":1}, {0,1}])
def test_late_bad_pair_is_atomic(bad):
    c=q.Circuit(4).h(0).checkpoint("before");before=c.to_qiskit()
    with pytest.raises(ValueError):c.cx(pairs=[(0,1),bad])
    assert c.to_qiskit()==before and c.checkpoints=={"before":1}

def test_infinite_pair_outer_and_inner_are_bounded(monkeypatch):
    c=q.Circuit(2)
    monkeypatch.setattr(QuantumCircuit,"cx",lambda *a,**k:pytest.fail("preflight must precede native append"))
    with pytest.raises(q.ResourceLimit):c.cx(pairs=itertools.repeat((0,1)))
    with pytest.raises(ValueError):c.cx(pairs=[itertools.cycle((0,1))])

@pytest.mark.parametrize("symbolic",[False,True])
def test_selection_preserves_wire_validation(symbolic):
    c=q.Circuit.symbolic(4) if symbolic else q.Circuit(4)
    c.h(iter([3,np.int64(1),0]))
    raw=QuantumCircuit(4);raw.h([3,1,0])
    assert c.to_qiskit()==raw
    for wires in ([3,3],[3,True],[3,4],[]):
        with pytest.raises(ValueError):c.h(iter(wires))
        assert c.to_qiskit()==raw

def test_subclass_gate_lookup_retained():
    class Custom(q.Circuit):
        lookups=0
        @property
        def gates(self):
            self.lookups+=1
            return super().gates
    c=Custom(4);c.h([0,2,1])
    assert c.lookups==3
