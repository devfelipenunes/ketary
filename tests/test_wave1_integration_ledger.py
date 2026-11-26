import json
import re
from pathlib import Path

def test_wave1_evidence_ledger():
    data=json.loads((Path(__file__).resolve().parents[1]/"docs"/"wave1-integration-ledger.json").read_text())
    assert data["schema_version"]==1
    assert [r["pr"] for r in data["entries"]]==[413,419,420]
    assert data["all_entries_same_file_tree"] is True
    assert len({r["sdk_run"] for r in data["entries"]})==3
    for row in data["entries"]:
        assert all(re.fullmatch(r"[a-f0-9]{40}",row[k]) for k in ("head","main"))
        assert row["head"]!=row["main"]
        assert row["dynamic_pass"]>=row["core_pass"]>0
        assert row["post_merge_run"] is None or row["post_merge_run"]!=row["sdk_run"]
    assert {r["classification"] for r in data["decisions"]}=={"confirmed_fixed","inconclusive","unsupported","negative"}
    assert all(r["evidence"] and r["decision"] for r in data["decisions"])
    assert data["exclusions"]
