"""Regression and native sequence oracles for ordered dynamic batches."""
import itertools

import pytest
import ketary as q
from qiskit import QuantumCircuit


def test_ordered_dynamic_batches_match_native():
    c=q.Circuit.classical(4,4).x(3)
    native=QuantumCircuit(4,4)
    native.x(3)
    assert c.measure(iter([3,0,2]), iter([1,3,0])) is c
    for wire,bit in [(3,1),(0,3),(2,0)]:
        native.measure(wire,bit)
    assert c.reset([2,3,0]) is c
    for wire in [2,3,0]:
        native.reset(wire)
    c.measure(3,1)
    native.measure(3,1)
    assert c.to_qiskit()==native


@pytest.mark.parametrize("wires,bits", [
    ([],[]), ([0,1],[0]), ([0],[0,1]), ([0,0],[0,1]),
    ([0,1],[1,1]), ([0,4],[0,1]), ([0,1],[0,4]),
    ([0,True],[0,1]), ([0,1],[0,True]), ({0,1},[0,1]),
    ([0,1],{0,1}), ([0],0), (0,[0]), ("01",[0,1]),
    ([0,1],itertools.repeat(0)),
])
def test_invalid_measurement_preflight(wires,bits,monkeypatch):
    c=q.Circuit.classical(4,4).h(0)
    before=c.to_qiskit()
    def forbidden(*a,**kw):
        pytest.fail("native measurement began before complete validation")
    monkeypatch.setattr(QuantumCircuit,"measure",forbidden)
    with pytest.raises(ValueError):
        c.measure(wires,bits)
    assert c.to_qiskit()==before


@pytest.mark.parametrize("wires", [[],[0,0],[0,4],[0,True],{0,1},"01"])
def test_invalid_reset_preflight(wires,monkeypatch):
    c=q.Circuit.classical(4,4).x(0)
    before=c.to_qiskit()
    def forbidden(*a,**kw):
        pytest.fail("native reset began before complete validation")
    monkeypatch.setattr(QuantumCircuit,"reset",forbidden)
    with pytest.raises(ValueError):
        c.reset(wires)
    assert c.to_qiskit()==before


@pytest.mark.parametrize("operation", ["measure","reset"])
def test_late_native_failure_does_not_mutate_source(operation,monkeypatch):
    c=q.Circuit.classical(3,3).x(0)
    c.register("data",[2,0])
    before=c.to_qiskit()
    original=getattr(QuantumCircuit,operation)
    calls=[]
    def fail_later(self,*a,**kw):
        calls.append(1)
        value=original(self,*a,**kw)
        if len(calls)==2:
            raise RuntimeError("injected native failure")
        return value
    monkeypatch.setattr(QuantumCircuit,operation,fail_later)
    with pytest.raises(RuntimeError):
        if operation=="measure":
            c.measure([2,0],[1,2])
        else:
            c.reset([2,0])
    assert len(calls)==2
    assert c.to_qiskit()==before and c.registers=={"data":(2,0)}


def test_explicit_classical_mode_required():
    c=q.Circuit(3)
    with pytest.raises(q.UnsupportedOperation):
        c.measure([0,1],[0,1])
    with pytest.raises(q.UnsupportedOperation):
        c.reset([0,1])


def test_dynamic_batches_aer_deterministic_oracle():
    pytest.importorskip("qiskit_aer")
    c=q.Circuit.classical(3,3).x(2)
    c.measure([2,0],[0,2]).reset([2,0]).measure(2,1)
    r=c.run_shots(shots=32,seed=42)
    assert r.counts=={"001":32}
    assert r.measurements==((2,2,0),(3,0,2),(6,2,1))
