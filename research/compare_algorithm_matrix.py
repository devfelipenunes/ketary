"""Strict same-runner joins; distinguish algorithm stages and inputs."""
import argparse
import csv
import json
from pathlib import Path
def key(r):
    return (r["name"],r["stage"],r.get("input",""),r.get("shots",0))
def compare(before,after):
    for field in ("seed","suite","repetitions","qiskit","aer","numpy"):
        if before[field]!=after[field]:raise ValueError(f"unmatched {field}")
    a={key(x):x for x in before["rows"]};b={key(x):x for x in after["rows"]}
    if len(a)!=len(before["rows"]) or len(b)!=len(after["rows"]) or not a.keys()<=b.keys():
        raise ValueError("unmatched or duplicate cases")
    if before["excluded"]!=after["excluded"]:raise ValueError("corpus exclusions differ")
    out=[]
    for k,row in b.items():
        old=a.get(k)
        if old and any(old[x]!=row[x] for x in ("n","original_gates","original_depth","gate_histogram")):
            raise ValueError("native circuit metadata differs")
        native=row["samples"]["native"]["median_ms"]
        old_sdk=old["samples"]["ketary"]["median_ms"] if old and "ketary" in old["samples"] else None
        for variant,sample in row["samples"].items():
            m=sample["median_ms"]
            out.append({"name":k[0],"stage":k[1],"input":k[2],"shots":k[3],"n":row["n"],
                        "original_gates":row["original_gates"],"lowered_gates":row.get("lowered_gates",""),
                        "variant":variant,"median_ms":m,"p95_ms":sample["p95_ms"],"p99_ms":sample["p99_ms"],
                        "qiskit_current_ms":native,"relative_to_qiskit":m/native,
                        "ketary_before_ms":old_sdk if old_sdk is not None else "",
                        "before_over_after":old_sdk/m if old_sdk is not None and variant=="ketary" else "",
                        "native_before_ms":old["samples"]["native"]["median_ms"] if old else "",
                        "seed":after["seed"]})
    return out
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("before",type=Path);p.add_argument("after",type=Path);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();rows=compare(json.loads(a.before.read_text()),json.loads(a.after.read_text()))
    with a.output.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps({"comparison_rows":len(rows),"matched_revision_cases":len(json.loads(a.before.read_text())["rows"])}))
