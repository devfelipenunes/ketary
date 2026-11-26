"""Conservative optimization must preserve full operators, including phase."""
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import ketary as q

@pytest.mark.parametrize("gate,wires",[("h",[0]),("x",[0]),("y",[0]),("z",[0]),("cx",[1,0]),("cz",[0,1]),("swap",[0,1]),("ccx",[0,1,2])])
def test_self_inverse_pairs(gate,wires):
    c=q.Circuit(3)
    getattr(c.gates,gate)(*wires)
    getattr(c.gates,gate)(*wires)
    d=c.optimize()
    assert c.resources.summary().gate_count==2
    assert d.resources.summary().gate_count==0
    c.test.equivalent(d).require()

@pytest.mark.parametrize("gate,adjoint",[("s","sdg"),("sdg","s"),("t","tdg"),("tdg","t")])
def test_phase_gate_inverses(gate,adjoint):
    c=q.Circuit(1)
    getattr(c.gates,gate)(0)
    getattr(c.gates,adjoint)(0)
    d=c.optimize()
    assert d.resources.summary().gate_count==0
    c.test.equivalent(d).require()

@pytest.mark.parametrize("gate",["rx","ry","rz"])
def test_rotation_inverses_and_near_miss(gate):
    c=q.Circuit(1)
    getattr(c.gates,gate)(.37,0)
    getattr(c.gates,gate)(-.37,0)
    assert c.optimize().resources.summary().gate_count==0
    c.test.equivalent(c.optimize()).require()
    d=q.Circuit(1)
    getattr(d.gates,gate)(.37,0)
    getattr(d.gates,gate)(-.37+1e-13,0)
    assert d.optimize().resources.summary().gate_count==2

def test_preserves_global_phase_and_nested_pairs():
    raw=QuantumCircuit(2,global_phase=.43)
    raw.h(0);raw.cx(0,1);raw.cx(0,1);raw.h(0);raw.rz(2*np.pi,1)
    c=q.from_qiskit(raw); d=c.optimize()
    assert d.resources.summary().gate_count==1
    np.testing.assert_allclose(Operator(raw).data,Operator(d.to_qiskit()).data,atol=1e-12,rtol=0)
    d.gates.x(0)
    assert c.to_qiskit()==raw

def test_different_wires_and_nonadjacent_not_removed():
    c=q.Circuit(2).gates.cx(0,1).gates.cx(1,0).gates.h(0).gates.z(0).gates.h(0)
    assert c.optimize().resources.summary().gate_count==5
    c.test.equivalent(c.optimize()).require()

@pytest.mark.parametrize("seed",[7,42,2026])
def test_seeded_full_operator_and_idempotence(seed):
    rng=np.random.default_rng(seed)
    c=q.Circuit(3)
    for _ in range(30):
        wire=int(rng.integers(0,3)); theta=float(rng.uniform(-3,3))
        c.gates.h(wire).gates.rx(theta,wire).gates.rx(-theta,wire)
        if rng.integers(0,2): c.gates.h(wire)
        else: c.gates.cx(wire,(wire+1)%3)
    d=c.optimize()
    c.test.equivalent(d,atol=1e-12).require()
    assert d.resources.summary().gate_count<c.resources.summary().gate_count
    assert d.optimize().to_qiskit()==d.to_qiskit()

def test_optimization_does_not_execute(monkeypatch):
    c=q.bell().gates.z(1).gates.z(1)
    def fail(*args,**kwargs): raise AssertionError("unexpected run")
    monkeypatch.setattr(q.Circuit,"run",fail)
    d=c.optimize()
    assert d.resources.summary().gate_count==2
