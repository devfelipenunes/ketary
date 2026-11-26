"""Bounded scaling study with paired timings and isolated process RSS.

CI is shared; no dedicated-host or superiority claim.
"""
import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
import resource
import numpy as np
import ketary as q
from qiskit.quantum_info import Operator

def worker(n,method,reps):
    a=q.ghz(n)
    b=a.copy().x(0).x(0)
    def run():
        if method=="dense":
            return a.test.metrics(b)["status"]
        if method=="samples":
            return a.test.compare(b,inputs=["0"*n,"+"*n],complete=False)["status"]
        if method=="external":
            return a.test.external_equivalence(b,deadline=10)["status"]
        raise ValueError("unknown method")
    expected="INCONCLUSIVE" if method=="samples" else "PASS"
    assert run()==expected
    samples=[]
    for _ in range(reps):
        start=time.perf_counter_ns()
        status=run()
        samples.append((time.perf_counter_ns()-start)/1e6)
        assert status==expected
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform.startswith("linux"):
        with open("/proc/self/status",encoding="utf-8") as f:
            fields={line.split(":",1)[0]:line.split(":",1)[1].strip() for line in f if ":" in line}
        peak=int(fields["VmHWM"].split()[0])
    return {"n":n,"method":method,"status":expected,"median_ms":statistics.median(samples),
            "p95_ms":float(np.percentile(samples,95)),"raw_ms":samples,"peak_rss_kib":peak}

def study(reps,external):
    rows=[]
    for n in (2,4,6,8,10,12,16,20):
        methods=(["dense"] if n<=8 else [])+(["samples"] if n<=12 else [])+(["external"] if external else [])
        for method in methods:
            output=subprocess.check_output([sys.executable,__file__,"--worker",str(n),method,"--repetitions",str(reps)],text=True)
            rows.append(json.loads(output))
    return {"scope":"GHZ plus inverse pair; methods have different guarantee strengths, no direct speedup claim",
            "commit":os.getenv("GITHUB_SHA"),"platform":platform.platform(),"repetitions":reps,"rows":rows}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--worker",nargs=2)
    p.add_argument("--external",action="store_true")
    p.add_argument("--repetitions",type=int,default=5)
    args=p.parse_args()
    if not 3<=args.repetitions<=30:
        p.error("repetitions must be 3..30")
    data=worker(int(args.worker[0]),args.worker[1],args.repetitions) if args.worker else study(args.repetitions,args.external)
    print(json.dumps(data,indent=2,allow_nan=False))
