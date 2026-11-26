"""Explicit norm, phase, report and trace scope oracles (#125 #131 #132)."""
import json
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit

@pytest.mark.parametrize("phase", [.31,-.8,np.pi])
def test_phase_metrics(phase):
    raw=QuantumCircuit(1,global_phase=phase)
    a=q.from_qiskit(raw);b=q.Circuit(1)
    strict=a.test.metrics(b)
    assert strict.status=="FAIL"
    assert strict.operator_norm==pytest.approx(abs(np.exp(1j*phase)-1),abs=1e-12)
    assert strict["process_fidelity"]==pytest.approx(1.)
    aligned=a.test.metrics(b,ignore_global_phase=True)
    assert aligned.status=="PASS" and aligned.operator_norm<1e-12
    assert a.test.equivalent(b,ignore_global_phase=True).status=="PASS"

def test_element_and_spectral_are_distinct():
    a=q.Circuit(1).h(0);b=q.Circuit(1)
    r=a.test.metrics(b,atol=1.8)
    # H-I has eigenvalues 0,-2; largest element is 1+1/sqrt(2).
    assert r["operator_norm"]==pytest.approx(2.)
    assert r["max_element_error"]==pytest.approx(1+1/np.sqrt(2))
    assert r.status=="FAIL" and a.test.equivalent(b,atol=1.8).status=="PASS"
    assert a.test.metrics(q.Circuit(2)).operator_norm is None

def test_zero_overlap_and_report_roundtrip():
    a=q.Circuit(1).x(0);b=q.Circuit(1)
    report=a.test.metrics(b,ignore_global_phase=True)
    assert report["process_fidelity"]==pytest.approx(0.)
    assert report.operator_norm==pytest.approx(2.)
    for value in (report,a.test.metrics(b,max_bytes=1),a.test.compare(b,inputs=["0"]),b.test.compare(b)):
        assert isinstance(value,dict)
        assert value.to_dict()==json.loads(value.to_json())==json.loads(value.render())
        assert value.status==value["status"]
        if value.status=="PASS":
            assert value.require() is value
        else:
            with pytest.raises(AssertionError):value.require()
    assert b.test.compare(b).evidence is None
    assert a.test.compare(b,inputs=["0"]).evidence.reproduce()["reproduced"]

def test_trace_alignment_scope_and_preflight(monkeypatch):
    a=q.Circuit(2).h(0).checkpoint("h").cx(0,1)
    b=q.Circuit(2).h(0).checkpoint("h").z(1).cx(0,1)
    report=a.debug.compare_checkpoints(b,[(0,0),("h","h"),(1,2),(2,3)])
    assert report.status=="PASS"
    assert len(report["checks"])==4
    assert report.to_dict()==json.loads(report.to_json())
    from ketary import _trace
    monkeypatch.setattr(_trace,"_Cursor",lambda *a,**k:pytest.fail("cursor constructed before invalid preflight"))
    for pairs in ([(1,1),(0,2)],[(1,1),(1,1)],[("h","h"),(1,1)],[(3,0)]):
        with pytest.raises(ValueError):a.debug.compare_checkpoints(b,pairs)
    with pytest.raises(ValueError):a.debug.compare_checkpoints(b,[(0,0)],ignore_global_phase=1)
    for kwargs in ({"max_steps":0},{"max_bytes":1}):
        assert a.debug.compare_checkpoints(b,[(2,3)],**kwargs).status=="UNSUPPORTED"
