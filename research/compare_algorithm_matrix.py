"""Strict same-runner joins; distinguish algorithm stages and inputs."""
import argparse
import csv
import json
import math
import statistics
from pathlib import Path
def key(r):
    return (r["name"],r["stage"],r.get("input",""),r.get("shots",0))
def percentile(values,p):
    values=sorted(values)
    position=(len(values)-1)*p
    lo=math.floor(position)
    hi=math.ceil(position)
    return values[lo]+(values[hi]-values[lo])*(position-lo)

def positive(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>0

def equivalent(value,expected):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and math.isclose(value,expected,rel_tol=1e-10,abs_tol=1e-12)

def validate(report):
    reps=report["repetitions"]
    if type(reps) is not int or not 3<=reps<=100:
        raise ValueError("invalid repetitions")
    if not report["rows"]:
        raise ValueError("empty benchmark report")
    for row in report["rows"]:
        samples=row["samples"]
        variants=set(samples)
        if "native" not in variants or variants!=set(row["validation"]) or variants!=set(row["paired_ratio_to_native"]):
            raise ValueError("missing native, validation or paired variant")
        orders=row["orders"]
        if len(orders)!=reps or any(len(order)!=len(variants) or set(order)!=variants for order in orders):
            raise ValueError("invalid randomized trial orders")
        for name,sample in samples.items():
            raw=sample["raw_ms"]
            if len(raw)!=reps or not all(positive(x) for x in raw):
                raise ValueError("invalid raw timing samples")
            med=statistics.median(raw)
            expected={"median_ms":med,"p95_ms":percentile(raw,.95),"p99_ms":percentile(raw,.99),
                      "min_ms":min(raw),"max_ms":max(raw),"mean_ms":statistics.mean(raw),
                      "stdev_ms":statistics.stdev(raw),"mad_ms":statistics.median(abs(x-med) for x in raw)}
            for field,value in expected.items():
                if not equivalent(sample[field],value):
                    raise ValueError(f"inconsistent {field} for {name}")
            native=samples["native"]["raw_ms"]
            if len(native)!=reps or not all(positive(x) for x in native):
                raise ValueError("invalid native samples")
            paired=[x/y for x,y in zip(raw,native,strict=True)]
            ratios=row["paired_ratio_to_native"][name]
            if not equivalent(ratios["median"],statistics.median(paired)) or not equivalent(ratios["p95"],percentile(paired,.95)):
                raise ValueError("inconsistent paired ratios")
    return report

def compare(before,after):
    validate(before)
    validate(after)
    for field in ("seed","suite","repetitions","python","qiskit","aer","numpy","platform","affinity"):
        if before[field]!=after[field]:raise ValueError(f"unmatched {field}")
    a={key(x):x for x in before["rows"]};b={key(x):x for x in after["rows"]}
    if len(a)!=len(before["rows"]) or len(b)!=len(after["rows"]) or not a.keys()<=b.keys():
        raise ValueError("unmatched or duplicate cases")
    if before["excluded"]!=after["excluded"]:raise ValueError("corpus exclusions differ")
    if any(k[1] not in {"execute_common_basis","lowering","import"} for k in b.keys()-a.keys()):
        raise ValueError("unexpected unmatched candidate case")
    out=[]
    for k,row in b.items():
        old=a.get(k)
        if old and any(old.get(x)!=row.get(x) for x in ("n","original_gates","original_depth","original_two_plus","gate_histogram","state_bytes","family","source_blob","removed","sdk_import_path")):
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
