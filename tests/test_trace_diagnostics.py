"""Aligned trace diagnosis and bounded comparison."""
import pytest
from qiskit import QuantumCircuit
import ketary as q

def test_first_observed_divergence_and_reconvergence():
    reference=q.Circuit(1).gates.h(0).gates.x(0).gates.x(0)
    observed=q.Circuit(1).gates.h(0).gates.z(0).gates.z(0)
    assert reference.run().test.state(observed.run()).status=="PASS"
    diff=observed.debug.compare(reference)
    assert isinstance(diff,q.TraceComparison)
    assert diff.check.status=="FAIL"
    assert diff.step_index==2
    assert (diff.actual_operation,diff.reference_operation)==("z","x")
    assert diff.actual_wires==diff.reference_wires==(0,)

def test_matching_trace_not_operator_equivalence():
    a=q.Circuit(1).gates.z(0)
    b=q.Circuit(1).gates.rz(0,0)
    assert a.debug.compare(b).check.status=="PASS"
    assert a.test.equivalent(b).status=="FAIL"

def test_phase_at_initial_checkpoint():
    a=q.Circuit(1)
    b=q.from_qiskit(QuantumCircuit(1,global_phase=.5))
    assert a.debug.compare(b).check.status=="PASS"
    diff=a.debug.compare(b,ignore_global_phase=False)
    assert diff.check.status=="FAIL" and diff.step_index==0

def test_unsupported_alignment_and_budget(monkeypatch):
    a=q.bell()
    def fail(*args,**kwargs): raise AssertionError("trace must not execute")
    monkeypatch.setattr(type(a.debug),"trace",fail)
    assert a.debug.compare(q.Circuit(2)).check.status=="UNSUPPORTED"
    assert a.debug.compare(q.Circuit(3)).check.status=="UNSUPPORTED"
    assert a.debug.compare(a,max_bytes=383).check.status=="UNSUPPORTED"
    assert a.debug.compare(a,max_steps=1).check.status=="UNSUPPORTED"
    c=q.Circuit(9)
    assert c.debug.compare(c).check.status=="UNSUPPORTED"

def test_exact_combined_payload_and_isolation():
    a=q.bell()
    before=a.to_qiskit()
    diff=a.debug.compare(q.bell(),max_bytes=384,max_steps=2)
    diff.check.require()
    assert diff.step_index is None and a.to_qiskit()==before

@pytest.mark.parametrize("kwargs",[{"atol":-1},{"max_bytes":0},{"max_steps":-1},{"ignore_global_phase":1}])
def test_bad_comparison_arguments(kwargs):
    a=q.bell()
    with pytest.raises(ValueError): a.debug.compare(a,**kwargs)
