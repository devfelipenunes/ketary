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


@pytest.mark.parametrize("bits,paulis",[
    (["00","1"],["XX"]), (["00","0x"],["XX"]),
    (["00"],["XX","X"]), (["00"],["XX","XYz"]),
    (["00"],["XX","xy"]),
])
def test_evidence_preflights_every_label(monkeypatch,bits,paulis):
    r=q.bell().run()
    def forbidden(*a,**k):pytest.fail("snapshot query before complete label admission")
    monkeypatch.setattr(type(r.math),"amplitude",forbidden)
    monkeypatch.setattr(type(r.math),"expectation",forbidden)
    with pytest.raises(ValueError):r.evidence(bits=bits,paulis=paulis)

def test_evidence_preserves_valid_order_and_values():
    r=q.bell().run()
    out=r.evidence(bits=["11","00"],paulis=["ZZ","XX"])
    assert list(out["basis"])==["11","00"]
    assert list(out["expectations"])==["ZZ","XX"]
    assert out["basis"]["11"]["probability"]==pytest.approx(.5)
    assert out["expectations"]==pytest.approx({"ZZ":1.,"XX":1.})
    assert r.evidence()["basis"]=={}

@pytest.mark.parametrize("seed",[True,-1,1.5,"1"])
def test_marginal_sampling_seed_precedes_probability_work(monkeypatch,seed):
    r=q.bell().run()
    monkeypatch.setattr(type(r.math),"marginal_probabilities",
        lambda *a,**k:pytest.fail("marginal allocation before seed admission"))
    with pytest.raises(ValueError):r.sample(shots=8,wires=[0],seed=seed)

def test_marginal_sampling_valid_seed_and_order():
    import numpy as np
    r=q.Circuit(3).h(0).x(2).run()
    probabilities=r.math.marginal_probabilities([2,0])
    p=np.array(list(probabilities.values()))
    p/=p.sum()
    counts=np.random.default_rng(1101).multinomial(32,p)
    expected={key:int(v) for key,v in zip(probabilities,counts,strict=True) if v}
    got=r.sample(shots=32,seed=1101,wires=[2,0])
    assert got==expected and list(got)==list(expected)
