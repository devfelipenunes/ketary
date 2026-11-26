"""Check the bounded baseline evidence ledger without network or release claims."""
import json
import re
from pathlib import Path

def test_integrated_evidence_registry():
    path=Path(__file__).resolve().parents[1]/"docs"/"integration-evidence.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"]==1
    b=data["baseline"]
    for k in ("main_sha","candidate_sha"):
        assert re.fullmatch(r"[0-9a-f]{40}",b[k])
    assert b["main_sha"]!=b["candidate_sha"]
    assert b["same_file_tree"] is True
    assert b["exact_head_run"]["conclusion"]=="success"
    assert set(b["exact_head_run"]["jobs"])=={"tests","dynamic","dependency-review","external-verifier","benchmark","packaging"}
    assert b["exact_head_run"]["id"]>0
    assert b["post_merge_run"] is None or b["post_merge_run"]!=b["exact_head_run"]["id"]
    for name in ("core","dynamic"):
        assert b[name]["passed"]>0
        assert 0<=b[name]["coverage"]<=100
    ids=data["reconciliation"]
    closed=set(ids["closed_previously"])|set(ids["closed_current"])
    assert closed.isdisjoint(ids["still_open"])
    assert set(map(int,ids["open_reasons"]))==set(ids["still_open"])
    assert data["exclusions"]
    assert len({r["pr"] for r in data["historical"]})==len(data["historical"])
