"""Matched sparse-shot diagnostic; one fresh subprocess per sample (Linux RSS)."""
import argparse
import json
import os
import resource
import statistics
import subprocess
import sys
import time
import numpy as np
import ketary as q

def worker(n,shots,seed,mode):
    c=q.Circuit(n).h(range(n))
    r=c.run()
    baseline=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    start=time.perf_counter_ns()
    if mode=="sdk":
        counts=r.sample(shots=shots,seed=seed)
    else:
        p=np.abs(r.math.statevector())
        np.square(p,out=p);p/=p.sum()
        raw=np.random.default_rng(seed).multinomial(shots,p)
        counts={format(int(i),f"0{n}b"):int(raw[i]) for i in np.flatnonzero(raw)}
    elapsed=time.perf_counter_ns()-start
    return {"ns":elapsed,"baseline_peak_kib":baseline,"peak_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"counts":counts,"retained_outcomes":len(counts)}

def run(widths=(12,16,20),shots=8,repeats=5):
    if not sys.platform.startswith("linux"):
        raise RuntimeError("Linux ru_maxrss units required")
    rows=[]
    for n in widths:
        for i in range(repeats):
            pair={}
            for mode in (("sdk","reference") if i%2==0 else ("reference","sdk")):
                cmd=[sys.executable,__file__,"--worker",str(n),str(shots),str(302+i),mode]
                pair[mode]=json.loads(subprocess.check_output(cmd,text=True,env={**os.environ,"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1","MKL_NUM_THREADS":"1"},timeout=90))
            assert pair["sdk"]["counts"]==pair["reference"]["counts"]
            assert sum(pair["sdk"]["counts"].values())==shots
            rows.append({"width":n,"seed":302+i,"shots":shots,**pair})
    summary=[]
    for n in widths:
        for mode in ("sdk","reference"):
            selected=[r[mode] for r in rows if r["width"]==n]
            times=[r["ns"] for r in selected]
            summary.append({"width":n,"mode":mode,"p50_ns":statistics.median(times),"p95_ns":float(np.percentile(times,95)),"max_peak_kib":max(r["peak_kib"] for r in selected)})
    return {"scope":"shared host diagnostic; reference includes public snapshot copy; peak RSS includes process setup","affinity":sorted(os.sched_getaffinity(0)),"raw":rows,"summary":summary}

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--worker":
        n,shots,seed=map(int,sys.argv[2:5])
        print(json.dumps(worker(n,shots,seed,sys.argv[5])))
    else:
        p=argparse.ArgumentParser()
        p.add_argument("--quick",action="store_true")
        a=p.parse_args()
        print(json.dumps(run((10,12),8,2) if a.quick else run(),indent=2))
