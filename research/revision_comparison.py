"""Compare same-runner longitudinal diagnostics without pooling machines."""
import argparse
import json
from pathlib import Path

def summarize(before,after):
    if before["seed"]!=after["seed"] or before["repetitions"]!=after["repetitions"]:
        raise ValueError("unmatched experiment configuration")
    if before["qiskit"]!=after["qiskit"] or before["numpy"]!=after["numpy"]:
        raise ValueError("unmatched native versions")
    def key(row):
        return tuple(sorted((k,v) for k,v in row.items() if k in ("case","n","gates","layers","queries")))
    a={key(row):row for row in before["cases"]}
    b={key(row):row for row in after["cases"]}
    if a.keys()!=b.keys() or len(a)!=len(before["cases"]) or len(b)!=len(after["cases"]):
        raise ValueError("unmatched workload definitions")
    rows=[]
    for k,old in a.items():
        new=b[k]
        if old["correctness"].get("instructions")!=new["correctness"].get("instructions"):
            raise ValueError("unmatched native instruction counts")
        variants={}
        for variant in old["samples"].keys()&new["samples"].keys():
            old_m=old["samples"][variant]["median_ms"]
            new_m=new["samples"][variant]["median_ms"]
            variants[variant]={"before_ms":old_m,"after_ms":new_m,"after_over_before":new_m/old_m,
                               "before_p95_ms":old["samples"][variant]["p95_ms"],
                               "after_p95_ms":new["samples"][variant]["p95_ms"]}
        row={**dict(k),"variants":variants}
        if "sdk_pairs" in new["samples"]:
            pair=new["samples"]["sdk_pairs"]["median_ms"]
            row["new_pairs"]={"median_ms":pair,
                              "over_candidate_apply_each":pair/new["samples"]["sdk_apply_each"]["median_ms"],
                              "over_candidate_native":pair/new["samples"]["native"]["median_ms"]}
        rows.append(row)
    return {"scope":"same shared runner, separate revision processes; diagnostic only",
            "before_commit":before["commit"],"after_commit":after["commit"],
            "seed":before["seed"],"repetitions":before["repetitions"],"cases":rows}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("before",type=Path)
    p.add_argument("after",type=Path)
    a=p.parse_args()
    print(json.dumps(summarize(json.loads(a.before.read_text()),json.loads(a.after.read_text())),
                     indent=2,allow_nan=False))
