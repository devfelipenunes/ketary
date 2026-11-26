import json
import pytest
import ketary as q

def test_ladder_never_promotes_samples_to_universal_pass():
    a=q.Circuit(1)
    b=q.Circuit(1).z(0)
    assert a.test.compare(b,inputs=["0"],complete=False)["status"]=="INCONCLUSIVE"
    assert a.test.compare(b,inputs=["0"])["status"]=="FAIL"
    report=a.test.compare(b,inputs=["+"])
    assert report["status"]=="FAIL"
    assert report["samples"][0]["distribution_tv"]==pytest.approx(0)
    assert a.test.compare(a)["status"]=="PASS"
    assert q.Circuit(9).test.compare(q.Circuit(9),inputs=["0"*9])["status"]=="INCONCLUSIVE"

def test_evidence_reproduction_and_minimization():
    a=q.Circuit(1).x(0).x(0).z(0)
    b=q.Circuit(1)
    report=a.test.compare(b,inputs=["+"])
    artifact=q.Evidence.from_json(json.dumps(report["evidence"]))
    assert artifact.reproduce()["reproduced"]
    reduced=artifact.minimize(max_attempts=16)
    assert reduced["after_gates"]<reduced["before_gates"]
    assert q.Evidence.from_json(json.dumps(reduced["evidence"])).reproduce()["reproduced"]
    assert a.inspect()["gate_count"]==3
    tampered=artifact.to_dict()
    tampered["data"]["input"]="0"
    with pytest.raises(ValueError,match="hash"):
        q.Evidence.from_json(json.dumps(tampered))

def test_semantic_diff_distinguishes_structure_and_phase():
    a=q.Circuit(1).h(0).h(0)
    b=q.Circuit(1)
    d=a.diff(b)
    assert not d["structure_equal"] and d["operator"]["status"]=="PASS"
    d=q.bell().diff(q.bell().z(0))
    assert d["zero_input"]["distribution_tv"]==pytest.approx(0)
    assert d["zero_input"]["fidelity"]==pytest.approx(0)
    assert d["operator"]["status"]=="FAIL"

def test_contract_checkpoint_and_incremental_alignment(monkeypatch):
    a=q.bell().z(0)
    c=q.Contract(2,expectations={"XX":1,"ZZ":1})
    report=a.debug.verify_checkpoints({2:c,3:c})
    assert report["first_nonpass"]==3
    assert report["checks"][0]["report"]["status"]=="PASS"
    assert report["checks"][1]["report"]["status"]=="FAIL"
    monkeypatch.setattr(type(a.debug),"checkpoint",lambda *a,**k:pytest.fail("prefix recomputation"))
    assert a.debug.compare_checkpoints(a,[(0,0),(2,2),(3,3)])["status"]=="PASS"

def test_inputs_validated_before_run(monkeypatch):
    a=q.bell()
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("invalid request executed"))
    for inputs in ([],["00","bad"],["00","00"],"00"):
        with pytest.raises(ValueError):
            a.test.compare(a,inputs=inputs)
