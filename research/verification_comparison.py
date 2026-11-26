"""Public deterministic calibration; no human/agent or novelty claims."""
import argparse
import json
import time
from importlib.metadata import version
from qiskit.quantum_info import Operator
import ketary as q

def cases():
    for i in range(12):
        a=q.Circuit(3).h(i%3).cx(i%3,(i+1)%3).rz(.1*(i+1),(i+2)%3)
        b=a.copy().x(i%3).x(i%3)
        yield f"equiv-{i:02}",a,b,"PASS"
        yield f"mutant-{i:02}",a,a.copy().x((i+1)%3),"FAIL"

def timed(fn):
    start=time.perf_counter_ns()
    value=fn()
    return value,(time.perf_counter_ns()-start)/1e6

def run(*,external=False):
    rows=[]
    for key,a,b,expected in cases():
        native,nt=timed(lambda:"PASS" if Operator(a.to_qiskit()).equiv(Operator(b.to_qiskit())) else "FAIL")
        result,kt=timed(lambda:a.test.compare(b,ignore_global_phase=True))
        row={"id":key,"expected":expected,"native":native,"ketary":result["status"],
             "native_ms":nt,"ketary_ms":kt,"has_witness":result["evidence"] is not None}
        if result["evidence"] is not None:
            row["reproduced"]=q.Evidence.from_json(json.dumps(result["evidence"])).reproduce()["reproduced"]
        if external:
            ext,et=timed(lambda:a.test.external_equivalence(b))
            row.update(qcec=ext["status"],qcec_ms=et,qcec_result=ext)
        rows.append(row)
    return {"scope":"24 authored calibration cases; single-run timings, not performance benchmark",
            "versions":{k:version(k) for k in ("ketary","qiskit","numpy")},
            "rows":rows,"native_correct":sum(r["native"]==r["expected"] for r in rows),
            "ketary_correct":sum(r["ketary"]==r["expected"] for r in rows),
            "external_correct":sum(r.get("qcec")==r["expected"] for r in rows) if external else None,
            "witnesses":sum(r["has_witness"] for r in rows),
            "reproduced":sum(r.get("reproduced",False) for r in rows)}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--external",action="store_true")
    args=p.parse_args()
    data=run(external=args.external)
    print(json.dumps(data,indent=2,allow_nan=False))
    assert data["native_correct"]==data["ketary_correct"]==24
    assert data["witnesses"]==data["reproduced"]==12
    if args.external:
        assert data["external_correct"]==24
