"""Isolated-process, pinned-CPU sparse-shot diagnostics. Linux only.

A pinned shared CI core is not a dedicated machine. Historical sampling uses
the same private snapshot as the current path; no public snapshot copy cost.
"""
import argparse
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
import numpy as np
import ketary as q
from research.sampling_dispatch import previous

def worker(n,layers,shots,seed,route,cpu):
    os.sched_setaffinity(0,{cpu})
    c=q.Circuit(n)
    for k in range(layers):
        c.ry(.31+.07*k,range(n)).cx(pairs=q.chain(range(n)))
    r=c.run()
    baseline=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t=time.perf_counter_ns()
    counts=r.sample(shots=shots,seed=seed) if route=="current" else previous(r,shots,seed)
    ns=time.perf_counter_ns()-t
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return dict(ns=ns,baseline_peak_kib=baseline,peak_kib=peak,peak_increment_kib=peak-baseline,
                affinity=sorted(os.sched_getaffinity(0)),state_payload_bytes=16*(1<<n),
                dense_probability_and_count_payload_bytes=16*(1<<n),retained_outcomes=len(counts),counts=list(counts.items()),
                logical_depth=c.to_qiskit().depth())

def run(quick=False):
    if not sys.platform.startswith("linux"):raise RuntimeError("Linux affinity and KiB RSS required")
    cpus=sorted(os.sched_getaffinity(0));cpu=cpus[0]
    widths=(10,12) if quick else (12,16,20)
    layers=(1,) if quick else (1,4)
    shots_set=(8,) if quick else (1,32)
    reps=2 if quick else 7
    raw=[];summary=[]
    env={**os.environ,"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1","MKL_NUM_THREADS":"1","RAYON_NUM_THREADS":"1"}
    for n in widths:
        for depth in layers:
            for shots in shots_set:
                group=[]
                for i in range(reps):
                    row=dict(width=n,layers=depth,shots=shots,seed=302+i)
                    order=("current","previous") if i%2==0 else ("previous","current")
                    row["trial_order"]=order
                    for route in order:
                        command=[sys.executable,"-m","research.closure_sampling_pinned","--worker",str(n),str(depth),str(shots),str(302+i),route,str(cpu)]
                        row[route]=json.loads(subprocess.check_output(command,text=True,env=env,timeout=120))
                    assert row["current"]["counts"]==row["previous"]["counts"]
                    assert sum(v for _,v in row["current"]["counts"])==shots
                    assert all(row[k]["affinity"]==[cpu] and row[k]["retained_outcomes"]<=shots for k in order)
                    raw.append(row);group.append(row)
                for route in ("current","previous"):
                    rows=[r[route] for r in group];times=[r["ns"] for r in rows]
                    summary.append(dict(width=n,layers=depth,shots=shots,route=route,p50_ns=statistics.median(times),
                                        p95_ns=float(np.percentile(times,95)),max_peak_kib=max(r["peak_kib"] for r in rows),
                                        max_increment_kib=max(r["peak_increment_kib"] for r in rows)))
    return dict(scope="pinned-core diagnostic; shared host unless separate authorization and isolation evidence supplied; RSS high-water includes setup",
                host=platform.platform(),original_affinity=cpus,selected_cpu=cpu,raw=raw,summary=summary)

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--worker":
        n,layers,shots,seed=map(int,sys.argv[2:6])
        print(json.dumps(worker(n,layers,shots,seed,sys.argv[6],int(sys.argv[7]))))
    else:
        p=argparse.ArgumentParser();p.add_argument("--quick",action="store_true")
        print(json.dumps(run(p.parse_args().quick),indent=2,allow_nan=False))
