"""Pinned isolated retained-state and conversion diagnostics; shared CI only."""
import argparse,json,os,platform,random,resource,subprocess,sys,time
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from research.circuit_rewrite_ladder import stats
from importlib.metadata import version

def worker(n,depth,count,seed,route):
    cpu=min(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpu})
    rng=np.random.default_rng(seed);angles=rng.uniform(-.9,.9,(depth,n))
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    expected=v.copy()
    # Independent Ry axis contractions, no native expected-state construction.
    for row in angles:
        for w,t in enumerate(row):
            a=np.cos(t/2);b=np.sin(t/2)
            shaped=expected.reshape(-1,2,1<<w)
            lo=shaped[:,0,:].copy();hi=shaped[:,1,:].copy()
            shaped[:,0,:]=a*lo-b*hi;shaped[:,1,:]=b*lo+a*hi
    before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t0=time.perf_counter_ns()
    c=q.Circuit(n) if route=="sdk" else QuantumCircuit(n)
    for row in angles:
        for w,t in enumerate(row):c.ry(float(t),w)
    t1=time.perf_counter_ns()
    if route=="sdk":results=c.run_many([v]*count)
    else:results=tuple(Statevector(v).evolve(c) for _ in range(count))
    t2=time.perf_counter_ns()
    states=tuple(r.math.statevector() if route=="sdk" else r.data.copy() for r in results)
    t3=time.perf_counter_ns();peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    for state in states:np.testing.assert_allclose(state,expected,atol=1e-9,rtol=0)
    return dict(n=n,depth=depth,count=count,seed=seed,route=route,cpu=cpu,affinity=sorted(os.sched_getaffinity(0)),baseline_hwm_kib=before,peak_hwm_kib=peak,output_bytes=sum(s.nbytes for s in states),stages_ms=[(t1-t0)/1e6,(t2-t1)/1e6,(t3-t2)/1e6])

def study():
    if sys.platform!="linux":raise RuntimeError("Linux affinity/RSS protocol")
    env=dict(os.environ,OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1")
    rng=random.Random(83119);rows=[]
    for n,depth,count in ((8,4,1),(8,16,8),(12,4,8),(16,8,8)):
        raw={"sdk":[],"native":[]}
        for seed in (83119,83131,83171):
            for route in rng.sample(list(raw),2):
                args=[sys.executable,"-m","research.alpha_third_rss","--worker",str(n),str(depth),str(count),str(seed),route]
                raw[route].append(json.loads(subprocess.check_output(args,env=env,text=True,timeout=120)))
        assert len({r["output_bytes"] for v in raw.values() for r in v})==1
        rows.append(dict(n=n,depth=depth,count=count,routes={k:dict(raw=v,stages=[stats([r["stages_ms"][i] for r in v]) for i in range(3)]) for k,v in raw.items()}))
    return dict(scope="isolated same retained output, per-worker CPU pin, HWM includes imports and oracle; no dedicated host or physical memory claim",python=sys.version,platform=platform.platform(),qiskit=version("qiskit"),rows=rows)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--worker",nargs=5);a=p.parse_args()
    print(json.dumps(worker(*map(int,a.worker[:4]),a.worker[4]) if a.worker else study(),indent=2,allow_nan=False))
