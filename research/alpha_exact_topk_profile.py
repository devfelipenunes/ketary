"""Compare installed top-k with the old public output, including formatting."""
import argparse
import hashlib
import heapq
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
import numpy as np
import ketary as q
from research.circuit_rewrite_ladder import stats

def old(r,k):
    data=r._data
    ranked=heapq.nlargest(min(k,len(data)),range(len(data)),key=lambda i:(abs(data[i])**2,-i))
    return {format(i,f"0{r.num_qubits}b"):float(abs(data[i])**2/r._norm_sq) for i in ranked}

def fixture(n,seed):
    rng=np.random.default_rng(seed);v=np.empty(1<<n,dtype=np.complex128)
    for i in range(0,len(v),8192):
        s=v[i:i+8192];s.real=rng.normal(size=s.size);s.imag=rng.normal(size=s.size)
    v/=np.sqrt(np.vdot(v,v).real)
    return q.Result(v)

def run(seed,reps):
    rng=random.Random(seed);rows=[]
    for n in (10,14,18):
        r=fixture(n,seed)
        for k in (1,8,16,32,64):
            expected=list(old(r,k).items())
            routes={"baseline":lambda:old(r,k),"candidate":lambda:r.math.top_probabilities(k=k)}
            timings={name:[] for name in routes}
            for _ in range(reps):
                for name in rng.sample(list(routes),len(routes)):
                    t=time.perf_counter_ns();actual=routes[name]();dt=(time.perf_counter_ns()-t)/1e6
                    assert list(actual.items())==expected
                    timings[name].append(dt)
            rows.append(dict(n=n,k=k,seed=seed,paths={name:stats(v) for name,v in timings.items()}))
    return rows

def hwm():
    with open("/proc/self/status") as f:
        return int(next(line for line in f if line.startswith("VmHWM:")).split()[1])

def worker(n,seed,route):
    r=fixture(n,seed);before=hwm()
    t=time.perf_counter_ns()
    result=old(r,32) if route=="baseline" else r.math.top_probabilities(k=32)
    dt=(time.perf_counter_ns()-t)/1e6
    peak=hwm()
    digest=hashlib.sha256(json.dumps(list(result.items())).encode()).hexdigest()
    return dict(n=n,seed=seed,route=route,before_hwm_kib=before,peak_hwm_kib=peak,
                resource_peak_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                elapsed_ms=dt,digest=digest)

def isolated():
    if platform.system()!="Linux":raise RuntimeError("Linux process HWM required")
    env=dict(os.environ,OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1")
    configs=[(n,s,r) for n in (18,20) for s in (1101,2202,3303) for r in ("baseline","candidate")]
    random.Random(1101).shuffle(configs);out=[]
    for n,s,r in configs:
        out.append(json.loads(subprocess.check_output([sys.executable,"-m","research.alpha_exact_topk_profile",
            "--worker",r,"--n",str(n),"--seed",str(s)],env=env,text=True)))
    for n in (18,20):
        for seed in (1101,2202,3303):
            assert len({r["digest"] for r in out if r["n"]==n and r["seed"]==seed})==1
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=5)
    p.add_argument("--rss",action="store_true");p.add_argument("--worker",choices=("baseline","candidate"))
    p.add_argument("--n",type=int,choices=(18,20),default=18);p.add_argument("--seed",type=int,default=1101)
    a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps(worker(a.n,a.seed,a.worker) if a.worker else dict(
        scope="exact public ordered output; Linux HWM after fixture includes lifetime peak, not allocator usage",
        rows=[r for seed in (1101,2202,3303) for r in run(seed,a.reps)],
        isolated_rss=isolated() if a.rss else []),indent=2,allow_nan=False))
