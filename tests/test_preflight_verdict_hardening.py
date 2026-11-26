"""Preflight contracts and missing optional distribution regression tests."""
import importlib.metadata
import sys
import types
import pytest
import ketary as q

@pytest.mark.parametrize("probabilities",[
    {"00":.5,"11":2.}, {"00":.5,"1":.5},
    {"00":.5,"11":float("nan")}, {"00":.5,"11":True},
])
def test_verify_preflights_all_probability_predicates(monkeypatch,probabilities):
    result=q.bell().run()
    def forbidden(*a,**k):pytest.fail("evaluated predicate before complete preflight")
    monkeypatch.setattr(type(result.test),"normalized",forbidden)
    monkeypatch.setattr(type(result.test),"probability",forbidden)
    with pytest.raises(ValueError):result.verify(probabilities=probabilities,normalized=True)

def test_verify_preserves_order_and_empty_legacy_contract():
    r=q.bell().run()
    report=r.verify(probabilities={"11":.5,"00":.5},expectations={"XX":1.},normalized=True)
    assert report.status=="PASS"
    assert list(report["checks"])==["normalized","probability:11","probability:00","expectation:XX"]
    assert r.verify().status=="UNSUPPORTED"

def test_external_missing_distribution_fails_closed(monkeypatch):
    mqt=types.ModuleType("mqt")
    def forbidden(*a,**k):pytest.fail("called unqualified optional backend")
    mqt.qcec=types.SimpleNamespace(verify_with_hard_timeout=forbidden)
    monkeypatch.setitem(sys.modules,"mqt",mqt)
    def missing(name):raise importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(importlib.metadata,"version",missing)
    report=q.bell().test.external_equivalence(q.bell())
    assert report.status=="UNSUPPORTED"
    assert "metadata" in report["reason"]

def test_external_wrong_circuit_type_is_not_backend_failure():
    with pytest.raises(TypeError):q.bell().test.external_equivalence(object())

def test_comparison_width_type_and_work_preflight(monkeypatch):
    a=q.bell()
    def forbidden(*a,**k):pytest.fail("simulation before preflight")
    monkeypatch.setattr(q.Circuit,"run",forbidden)
    with pytest.raises(TypeError):a.test.compare(object())
    with pytest.raises(ValueError):a.test.compare(q.Circuit(3))
    with pytest.raises(q.ResourceLimit):a.test.compare(q.Circuit(2),max_bytes=1)
    with pytest.raises(ValueError):a.test.compare(a,complete=1)
    with pytest.raises(ValueError):a.test.compare(a,ignore_global_phase=1)

def test_comparison_invalid_mode_rejected():
    with pytest.raises(q.UnsupportedOperation):q.bell().test.compare(q.Circuit.classical(2,2))

def test_semantic_diff_keeps_structure_distinct_from_zero_input():
    a=q.Circuit(2).z(0);b=q.Circuit(2)
    report=a.diff(b)
    assert not report.structure_equal
    assert report.zero_input["state_l2"]==0
    assert report.operator["status"]=="FAIL"
