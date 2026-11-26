"""Guard a frozen admitted surface and deterministic coverage evidence."""
import json
from pathlib import Path
import pytest
from research.coverage_evidence import build

ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/"docs"/name).read_text())

def admitted_surface(registry,policy):
    current={k:set(v) for k,v in registry["baseline_surface"].items()}
    decisions={v["id"]:v for v in policy["candidates"]}
    added=set()
    for row in registry["admissions"]:
        assert set(row)=={"symbol","category","decision","mode","owner_approval","ci"}
        symbol=row["symbol"]
        assert symbol not in added and all(symbol not in v for v in current.values())
        decision=decisions[row["decision"]]
        assert decision["decision"]=="promote" and all(v is True for v in decision["gates"].values())
        assert row["mode"] in ("bound","symbolic","dynamic","snapshot","all","native","artifact")
        assert row["owner_approval"] in decision["evidence"] and row["ci"] in decision["evidence"]
        assert row["owner_approval"]!=row["ci"]
        current[row["category"]].add(symbol);added.add(symbol)
    return current

def test_admitted_public_surface_matches_lifecycle():
    expected=admitted_surface(read("api-admission-baseline.json"),read("api-decisions.json"))
    assert expected=={k:set(v) for k,v in read("api-surface.json").items()}
    assert set(read("api-lifecycle.json")["entries"])==set().union(*expected.values())

def test_unqualified_addition_is_rejected():
    registry=read("api-admission-baseline.json");registry["admissions"]=[{"symbol":"Circuit.unreviewed","category":"Core","decision":"automatic_uncompute","mode":"bound","owner_approval":"none","ci":"none"}]
    with pytest.raises(AssertionError):admitted_surface(registry,read("api-decisions.json"))

def test_coverage_scope_and_baseline_counts():
    baseline=read("coverage-count-baseline.json")
    assert all(len(v["modules"])==26 for v in baseline["scopes"].values())
    raw={"files":{"src/ketary/_result.py":{"summary":{"num_statements":20,"num_branches":8,"percent_covered":80.},"missing_lines":[2,1],"missing_branches":[[3,5],[3,4]]}}}
    for scope in ("core","dynamic"):
        result=build(raw,baseline,scope)
        assert result==build(raw,baseline,scope)
        assert result["baseline_job"]==baseline["scopes"][scope]["job"]
        row=next(r for r in result["rows"] if r["module"]=="_result.py")
        assert row["current"]["missing_lines"]==[1,2]
        assert row["missing_line_delta"]==2-baseline["scopes"][scope]["modules"]["_result.py"]["missing_lines"]
        assert "missing_branch_delta" not in row
    with pytest.raises(ValueError):build(raw,baseline,"external")
