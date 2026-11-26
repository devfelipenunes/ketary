import numpy as np
import pytest
from qiskit import QuantumCircuit
import ketary as q

def test_distribution_is_not_state_equivalence():
    a=q.bell().run()
    b=q.bell().gates.z(0).run()
    a.test.distribution(b).require()
    assert a.test.state(b).status=="FAIL"
    assert a.test.fidelity(b).status=="FAIL"

def test_state_global_phase_modes():
    a=q.Result([1,0]); b=q.Result([1j,0])
    a.test.state(b).require()
    assert a.test.state(b,ignore_global_phase=False).status=="FAIL"

def test_distribution_distance():
    a=q.Result([1,0]); b=q.Result([0,1])
    assert a.test.distribution(b).actual==pytest.approx(1)
    assert a.test.distribution(b).status=="FAIL"
    with pytest.raises(ValueError): a.test.distribution(q.bell().run())

def test_expectation_assertions():
    r=q.bell().run()
    r.test.expectation("YY",-1).require()
    assert r.test.expectation("YY",1).status=="FAIL"
    with pytest.raises(ValueError): r.test.expectation("YY",2)

def test_operator_is_not_zero_state_comparison():
    a=q.Circuit(1)
    b=q.Circuit(1).gates.z(0)
    a.run().test.state(b.run()).require()
    assert a.test.equivalent(b).status=="FAIL"

def test_operator_global_phase_strict_default():
    a=q.Circuit(1)
    b=q.from_qiskit(QuantumCircuit(1,global_phase=np.pi))
    assert a.test.equivalent(b).status=="FAIL"
    a.test.equivalent(b,ignore_global_phase=True).require()

def test_operator_inverse_and_no_reexecution(monkeypatch):
    c=q.Circuit(2).gates.h(0).gates.cx(0,1).gates.rx(.2,1)
    d=c.compose(c.inverse())
    def fail(*args,**kwargs): raise AssertionError("unexpected execution")
    monkeypatch.setattr(q.Circuit,"run",fail)
    d.test.equivalent(q.Circuit(2)).require()

def test_operator_limits_before_construction(monkeypatch):
    from qiskit.quantum_info import Operator
    def fail(*args,**kwargs): raise AssertionError("unexpected allocation")
    monkeypatch.setattr(Operator,"__init__",fail)
    a=q.Circuit(9)
    check=a.test.equivalent(a)
    assert check.status=="UNSUPPORTED"
    assert check.actual is None
    with pytest.raises(AssertionError): check.require()
    b=q.Circuit(2)
    assert b.test.equivalent(b,max_bytes=511).status=="UNSUPPORTED"
    assert b.test.equivalent(q.Circuit(1)).status=="FAIL"

@pytest.mark.parametrize("bad",[float("nan"),float("inf"),-1])
def test_invalid_tolerance(bad):
    c=q.Circuit(1)
    with pytest.raises(ValueError): c.test.equivalent(c,atol=bad)
    with pytest.raises(ValueError): c.run().test.state(c.run(),atol=bad)

def test_no_implicit_truthiness():
    c=q.Circuit(9)
    with pytest.raises(TypeError): bool(c.test.equivalent(c))
