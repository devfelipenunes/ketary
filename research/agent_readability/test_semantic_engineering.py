import json
from dataclasses import FrozenInstanceError
import pytest
import ketary as q
from contracts import Contract
from semantic_engineering import semantic_inspect,diagnose,suggest_repair


def test_contract_snapshot_and_dual_views(monkeypatch):
    probs={"00":.5,"11":.5}
    contract=Contract(2,probabilities=probs,expectations={"XX":1,"ZZ":1},normalized=True)
    probs["00"]=0
    c=q.bell()
    good=c.run()
    bad=c.z(0).run()
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k: pytest.fail("implicit execution"))
    assert contract.verify(good).to_dict()["status"]=="PASS"
    report=contract.verify(bad)
    assert report.to_dict()["status"]=="FAIL"
    assert report.to_dict()["checks"]["probability:00"]["status"]=="PASS"
    assert report.to_dict()["checks"]["expectation:XX"]["status"]=="FAIL"
    assert "FAIL expectation:XX" in report.render()
    assert json.loads(report.compact_json())==report.to_dict()
    report.to_dict()["checks"].clear()
    assert len(report.to_dict()["checks"])==5
    assert report.to_dict()["contract_sha256"]==contract.verify(good).to_dict()["contract_sha256"]
    with pytest.raises(FrozenInstanceError):
        contract.atol=1


@pytest.mark.parametrize("kwargs",[
    {},{"probabilities":{"00":True}},{"probabilities":{"00":float("nan")}},
    {"probabilities":{"0":.5}},{"expectations":{"XY":2}},
    {"normalized":1},{"normalized":True,"atol":-1},
    {"probabilities":{"zz":.2}},
])
def test_invalid_contract(kwargs):
    with pytest.raises(ValueError):
        Contract(2,**kwargs)


def test_contract_not_operator():
    c=Contract(1,probabilities={"0":1})
    a,b=q.Circuit(1),q.Circuit(1).z(0)
    assert c.verify(a.run()).to_dict()["status"]=="PASS"
    assert c.verify(b.run()).to_dict()["status"]=="PASS"
    assert a.test.equivalent(b).status=="FAIL"
    with pytest.raises(ValueError):
        c.verify(q.Circuit(2).run())
    with pytest.raises(TypeError):
        c.verify(a)


def test_inspection_dependencies_without_run(monkeypatch):
    c=q.Circuit(3).h(0).x(2).cx(0,1).cx(2,1)
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k: pytest.fail("implicit execution"))
    r=semantic_inspect(c)
    assert r["dependencies"]==[{"index":1,"predecessors":[]},{"index":2,"predecessors":[]},
                                {"index":3,"predecessors":[1]},{"index":4,"predecessors":[2,3]}]
    assert r["wire_operations"]=={"0":[1,3],"1":[3,4],"2":[2,4]}
    with pytest.raises(q.ResourceLimit):
        semantic_inspect(q.Circuit(9))


def test_diagnosis_phase_and_scope():
    a=q.bell().h(0).h(0)
    b=q.bell().h(0).z(0)
    # Separate equal distribution relative-phase case; alignment is unequal.
    ref=q.bell()
    obs=q.bell().z(0)
    r=diagnose(obs,ref,paulis=iter(["XX","ZZ"])).to_dict()
    assert r["checks"]["distribution"]["status"]=="PASS"
    assert r["checks"]["state"]["status"]=="FAIL"
    assert r["checks"]["operator"]["status"]=="FAIL"
    assert r["checks"]["expectation:XX"]["actual"]==pytest.approx(-1)
    assert r["trace"]["check"]["status"]=="UNSUPPORTED"
    assert r["hypothesis"]
    assert diagnose(b,a).to_dict()["trace"]["step_index"]==4
    assert diagnose(q.Circuit(1),q.Circuit(2)).to_dict()["status"]=="UNSUPPORTED"


@pytest.mark.parametrize("kind",["replace","delete","insert"])
def test_verified_single_edit(kind):
    reference=q.bell()
    observed={"replace":lambda:q.Circuit(2).h(0).cx(1,0),
              "delete":lambda:q.bell().z(0),
              "insert":lambda:q.Circuit(2).h(0)}[kind]()
    before=observed.to_json()
    report=suggest_repair(observed,reference)
    assert report["status"]=="VERIFIED"
    edit=report["candidates"][0]
    assert edit["edit"]==kind
    fixed=q.Circuit.from_json(edit["replay"])
    assert fixed.test.equivalent(reference).status=="PASS"
    assert observed.to_json()==before


def test_repair_abstains_and_already_equivalent():
    assert suggest_repair(q.bell(),q.bell())["status"]=="ALREADY_EQUIVALENT"
    assert suggest_repair(q.Circuit(1),q.Circuit(2))["status"]=="UNSUPPORTED"
    assert suggest_repair(q.bell().x(0),q.bell(),max_candidates=1)["status"]=="UNSUPPORTED"
    assert suggest_repair(q.Circuit(2).x(0).z(1),q.bell())["status"]=="NO_REPAIR"
    with pytest.raises(ValueError):
        suggest_repair(q.bell(),q.bell(),max_candidates=0)


def test_source_provenance_is_not_origin_proof():
    c=q.Circuit(2).h(0).cx(0,1)
    src="import ketary as q\nc=q.Circuit(2).h(0).cx(0,1)"
    assert semantic_inspect(c,source=src)["provenance"]["status"]=="MATCH"
    assert semantic_inspect(c,source=src.replace("cx(0,1)","cx(1,0)"))["provenance"]["status"]=="UNSUPPORTED"
    assert semantic_inspect(c,source="arbitrary()")["provenance"]["status"]=="UNSUPPORTED"


def test_read_only_tool_registry():
    from read_tools import ReadTools
    c=q.bell()
    tools=ReadTools({"bell":c,"error":q.bell().z(0)})
    manifest=tools.manifest()
    c.z(0)
    assert tools.verify("bell",{"00":.5},{"XX":1})["status"]=="PASS"
    assert tools.verify("error",{},{"XX":1})["status"]=="FAIL"
    assert tools.compare("error","bell",["XX"])["status"]=="FAIL"
    assert tools.inspect("bell")["circuit"]["gate_count"]==2
    assert tools.manifest()==manifest
    with pytest.raises(ValueError):
        tools.inspect("../unregistered")
    with pytest.raises(ValueError):
        tools.verify("bell",{}, {})
