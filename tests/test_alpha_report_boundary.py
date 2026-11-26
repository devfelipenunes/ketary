"""Same dictionary schemas, strict JSON and distinct verdict contracts."""
import json
import pytest
from ketary._reports import ComparisonReport,SemanticDiffReport,SnapshotReport

@pytest.mark.parametrize("cls",[ComparisonReport,SemanticDiffReport,SnapshotReport])
def test_json_contract(cls):
    raw={"scope":"fixture","details":{"nested":[1,2]},"status":"FAIL"}
    r=cls(raw)
    expected=json.dumps(raw,sort_keys=True,allow_nan=False)
    assert r.render()==r.to_json()==expected
    exported=r.to_dict();exported["details"]["nested"].append(3)
    assert r["details"]["nested"]==[1,2]
    r["details"]["nested"].append(4)
    assert r.to_dict()["details"]["nested"]==[1,2,4]
    r["nonfinite"]=float("nan")
    with pytest.raises(ValueError):r.to_json()

def test_semantic_diff_has_no_aggregate_verdict():
    r=SemanticDiffReport({"scope":"separate","structure_equal":False,"operator":{"status":"FAIL"},"zero_input":{"status":"PASS"}})
    assert not hasattr(r,"status") and not hasattr(r,"require")
    assert r.operator.status=="FAIL" and r.zero_input["status"]=="PASS"
    with pytest.raises(AssertionError):r.operator.require()

def test_verdict_report_preserves_override_and_identity():
    class Custom(ComparisonReport):
        def to_json(self):return '{"custom":true}'
    r=Custom(status="PASS")
    assert r.require() is r and r.render()=='{"custom":true}' and r.to_dict()=={"custom":True}
    r["status"]="FAIL"
    with pytest.raises(AssertionError,match="custom"):r.require()
