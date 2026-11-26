from pathlib import Path
import json
from research.architecture_inventory import inspect

ROOT=Path(__file__).resolve().parents[1]

def test_current_cycle_rationales_and_metrics():
    report=inspect()
    reasons=json.loads((ROOT/"docs"/"local-import-rationales.json").read_text())["rationales"]
    assert not report["eager_cycles"]
    assert report["cycles"]
    missing={f'{x["source"]}->{x["target"]}' for x in report["cyclic_local_import_sites"]}-reasons.keys()
    assert not missing,sorted(missing)
    assert all(reasons[f'{x["source"]}->{x["target"]}'] for x in report["cyclic_local_import_sites"])
    assert all(v["branch_nodes"]>=0 for v in report["module_stats"].values())
    assert all(len(g)>1 for g in report["exact_duplicate_body_groups"])

def test_inventory_is_deterministic():
    assert inspect()==inspect()
