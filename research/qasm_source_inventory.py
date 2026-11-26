"""Count source-level operations in a pinned local QASMBench checkout.

No external source is vendored; no network access or execution of upstream code.
Usage: python research/qasm_source_inventory.py /path/to/QASMBench
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

COMMIT="357b942396d5c2b7cbc1c229c585a6ef5ccaebac"
NAMES="adder_n4 bb84_n8 cat_state_n4 deutsch_n2 grover_n2 ising_n10 qaoa_n3 qaoa_n6 qec_sm_n5 qft_n4 simon_n6 teleportation_n3 variational_n4 vqe_n4 vqe_uccsd_n4 wstate_n3".split()

def count_source(source):
    text=re.sub(r"//[^\n]*","",source)
    custom=re.findall(r"\bgate\s+(\w+)[^{]*\{",text)
    body=re.sub(r"\bgate\s+\w+[^{]*\{[^}]*\}","",text,flags=re.S)
    ops=[]
    for raw in body.split(";"):
        statement=raw.strip()
        if not statement or re.match(r"^(OPENQASM|include|qreg|creg|opaque)\b",statement):
            continue
        match=re.match(r"^(?:if\s*\([^)]*\)\s*)?([a-zA-Z_]\w*)",statement)
        if not match:
            raise ValueError("unrecognized source statement")
        ops.append(match.group(1))
    return {"counts":dict(Counter(ops)),"custom":custom,"statements":len(ops),
            "adjacent_same_name":sum(a==b for a,b in zip(ops,ops[1:]))}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",type=Path)
    args=parser.parse_args()
    ref=subprocess.check_output(["git","-C",str(args.root),"rev-parse","HEAD"],text=True).strip()
    if ref!=COMMIT:
        raise SystemExit("checkout must match "+COMMIT)
    rows=[]
    for name in NAMES:
        path=f"small/{name}/{name}.qasm"
        # Read the immutable commit, not a potentially dirty working tree.
        source=subprocess.check_output(["git","-C",str(args.root),"show",f"{COMMIT}:{path}"],text=True)
        rows.append({"file":path,**count_source(source)})
    counts=Counter()
    for row in rows:
        counts.update(row["counts"])
    print(json.dumps({"commit":COMMIT,"files":rows,"counts":dict(counts),
        "statements":sum(x["statements"] for x in rows),
        "adjacent_same_name":sum(x["adjacent_same_name"] for x in rows)},indent=2))
if __name__=="__main__":
    main()
