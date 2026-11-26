import json
import pytest
import ketary as q
from qiskit.circuit.library import CXGate

def test_snapshot_report_preserves_schema_and_scope(monkeypatch):
    r=q.bell().run()
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("implicit execution"))
    report=r.verify(expectations={"XX":1})
    assert isinstance(report,q.SnapshotReport) and report.require() is report
    assert report.status==report["status"]=="PASS"
    assert report.to_dict()==json.loads(json.dumps(report))
    checks=report.checks
    checks.clear()
    assert report.checks
    assert r.verify().status=="UNSUPPORTED"
    with pytest.raises(AssertionError):
        r.verify(expectations={"XX":-1}).require()

def test_named_debug_lookup_and_alignment():
    a=q.bell().checkpoint("prepared")
    b=a.copy().z(0).checkpoint("changed")
    a.debug.checkpoint("prepared").result.test.expectation("XX",1).require()
    b.debug.checkpoint("changed").result.test.expectation("XX",-1).require()
    report=b.debug.compare_checkpoints(a,[("prepared","prepared"),("changed","prepared")])
    assert report.status=="FAIL" and report["checks"][-1]["observed_index"]==3
    with pytest.raises(ValueError):
        b.debug.checkpoint("missing")
    with pytest.raises(ValueError):
        b.debug.compare_checkpoints(a,[{"changed","prepared"}])
    with pytest.raises(ValueError):
        b.debug.compare_checkpoints(a,[("changed","prepared"),("prepared","prepared")])

@pytest.mark.parametrize("wires",[{0,1},frozenset({0,1}),{0:1,1:0},"01",b"01"])
def test_unordered_gate_mapping_rejected_atomically(wires):
    c=q.Circuit(2).h(0)
    before=c.to_json()
    for fn in (lambda:c.apply(q.bell(),wires=wires),lambda:c.compose(q.bell(),wires=wires),lambda:c.append(CXGate(),wires)):
        with pytest.raises(ValueError):
            fn()
        assert c.to_json()==before

def test_typed_decoders_preserve_legacy_keys():
    phase=q.decode_phase_estimation(q.phase_estimation(.375).run(),precision=3)
    assert isinstance(phase,q.PhaseEstimateReport)
    assert phase.require().phase==phase["phase"]==.375
    mask=q.decode_bernstein_vazirani(q.bernstein_vazirani("101").run())
    assert mask.label==mask["label"]=="101"
    assert mask.peak_probability==pytest.approx(1)
    tie=q.decode_phase_estimation(q.Circuit(2).h(0).run(),precision=1)
    assert tie.phase is None and tie.status=="INCONCLUSIVE"
    with pytest.raises(AssertionError):
        tie.require()

def test_external_report_is_separate(monkeypatch):
    import ketary._external as backend
    monkeypatch.setattr(backend,"qcec_compare",lambda *a,**k:{"status":"UNSUPPORTED","scope":"fixture"})
    result=q.bell().test.external_equivalence(q.bell())
    assert isinstance(result,q.ExternalVerificationReport)
    assert result.external_equivalence is None
    with pytest.raises(AssertionError):
        result.require()
