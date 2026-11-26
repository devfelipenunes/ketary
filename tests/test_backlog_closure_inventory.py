"""Offline closure routing checks, not a claim of current GitHub state."""
import json
from pathlib import Path

def test_backlog_routing_snapshot():
    data=json.loads((Path(__file__).resolve().parents[1]/"docs"/"backlog-closure-inventory.json").read_text())
    assert data["schema_version"]==1
    rows=[item for lane in data["lanes"].values() for item in lane]
    ids=[row["issue"] for row in rows]
    assert len(ids)==len(set(ids))==data["open_issue_count"]==138
    assert set(ids).isdisjoint(data["closed_in_cycle"])
    assert all(row["title"] for row in rows)
    assert set(data["lanes"])=={"external_and_qualification","performance","expressivity","integration","math_verification_native","architecture_api","applications"}
