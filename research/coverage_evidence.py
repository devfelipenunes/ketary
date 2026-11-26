"""Deterministic scope-matched coverage evidence, not test-quality ranking."""
import argparse
import json
from pathlib import Path
from research.coverage_gaps import gaps

def build(raw,baseline,scope):
    if scope not in ("core","dynamic") or scope not in baseline["scopes"]:
        raise ValueError("explicit matching coverage scope required")
    current=gaps(raw)
    before=baseline["scopes"][scope]["modules"]
    rows=[]
    for name in sorted(current.keys()|before.keys()):
        a=current.get(name);b=before.get(name)
        rows.append({"module":name,"status":"matched" if a and b else "added" if a else "removed",
                     "current":a,"baseline_counts":b,
                     "missing_line_delta":len(a["missing_lines"])-b["missing_lines"] if a and b else None})
    return {"schema_version":1,"scope":scope,"baseline_revision":baseline["revision"],
            "baseline_job":baseline["scopes"][scope]["job"],"rows":rows,
            "priority_order":sorted(current,key=lambda k:(-len(current[k]["missing_branches"]),-len(current[k]["missing_lines"]),k)),
            "limitations":"Raw current missing arcs and line numbers retained. Historical partial branches are not missing-arc counts; no arc delta inferred. Line-count deltas are not proof of regression after source changes."}

def main():
    p=argparse.ArgumentParser();p.add_argument("coverage",type=Path);p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--scope",required=True,choices=("core","dynamic"));p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    report=build(json.loads(a.coverage.read_text()),json.loads(a.baseline.read_text()),a.scope)
    a.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
if __name__=="__main__":main()
