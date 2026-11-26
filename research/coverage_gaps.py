"""Report coverage deficits deterministically, not a test-quality score."""
import argparse
import json
from pathlib import Path

def gaps(report):
    files=report["files"]
    out={}
    for path,entry in files.items():
        normalized=path.replace("\\","/")
        marker="src/ketary/"
        if marker not in normalized:continue
        name=normalized.split(marker,1)[1]
        if name in out:raise ValueError("duplicate module path")
        summary=entry["summary"]
        out[name]={"missing_lines":sorted(entry["missing_lines"]),
                   "missing_branches":sorted(entry.get("missing_branches",[])),
                   "statements":summary["num_statements"],
                   "branches":summary.get("num_branches",0),
                   "coverage_percent":summary["percent_covered"]}
    if not out:raise ValueError("no Ketary source coverage")
    return dict(sorted(out.items()))

def compare(current,baseline):
    # Line numbers can shift between revisions. Only counts are comparable
    # without a source diff; never assert a regression by line number alone.
    rows=[]
    for name in sorted(current.keys()|baseline.keys()):
        a=current.get(name);b=baseline.get(name)
        rows.append({"module":name,"status":"matched" if a and b else "added" if a else "removed",
                     "missing_line_delta":len(a["missing_lines"])-len(b["missing_lines"]) if a and b else None,
                     "missing_branch_delta":len(a["missing_branches"])-len(b["missing_branches"]) if a and b else None,
                     "coverage_percent_delta":a["coverage_percent"]-b["coverage_percent"] if a and b else None})
    return rows

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("coverage",type=Path)
    parser.add_argument("--baseline",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--scope",required=True,help="e.g. core or dynamic; compare only equal scopes")
    args=parser.parse_args()
    current=gaps(json.loads(args.coverage.read_text()))
    data={"scope":args.scope,"modules":current,
          "priority_order":sorted(current,key=lambda k:(-len(current[k]["missing_branches"]),-len(current[k]["missing_lines"]),k)),
          "limitations":"coverage identifies unexecuted paths; not mathematical correctness or independent review"}
    if args.baseline:data["comparison"]=compare(current,gaps(json.loads(args.baseline.read_text())))
    args.output.write_text(json.dumps(data,indent=2,allow_nan=False)+"\n")
if __name__=="__main__":main()
