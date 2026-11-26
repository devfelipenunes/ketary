"""Matched complete operator metrics, including construction and numerical proof."""
import argparse
import json
import random
import time
import numpy as np
import ketary as q
from qiskit.quantum_info import Operator
from research.circuit_rewrite_ladder import stats

def baseline(a,b):
    A,B=Operator(a._qc).data,Operator(b._qc).data
    overlap=np.vdot(B,A)
    fidelity=float(np.clip(abs(overlap)**2/A.shape[0]**2,0,1))
    delta=A-B
    spectral=float(np.linalg.norm(delta,ord=2))
    return (float(np.max(np.abs(delta))),float(np.linalg.norm(delta)),spectral,fidelity)

def run(seed,reps):
    rng=random.Random(seed)
    rows=[]
    for n in (3,5,7,8):
        a=q.Circuit(n)
        for i in range(n):a.ry(rng.uniform(-1,1),i)
        for i in range(n-1):a.cx(i,i+1)
        for same in (True,False):
            b=a.copy()
            if not same:b.rz(.07,n-1)
            def candidate():
                r=a.test.metrics(b)
                return tuple(r[k] for k in ("max_element_error","frobenius_norm","operator_norm","process_fidelity"))
            paths={"baseline":lambda:baseline(a,b),"candidate":candidate}
            expected=baseline(a,b)
            timings={k:[] for k in paths}
            for _ in range(reps):
                for name in rng.sample(list(paths),len(paths)):
                    start=time.perf_counter_ns();actual=paths[name]();elapsed=(time.perf_counter_ns()-start)/1e6
                    assert actual==expected
                    timings[name].append(elapsed)
            rows.append(dict(n=n,same=same,seed=seed,paths={k:stats(v) for k,v in timings.items()}))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=5);a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps({"scope":"complete operators on both sides; strict phase; baseline excludes report wrapper, candidate includes it","rows":[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]},indent=2,allow_nan=False))
