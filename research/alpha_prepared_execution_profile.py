"""Matched original and preflight-reusing batch execution."""
import argparse
import json
import random
import time
import numpy as np
import ketary as q
from ketary._execution import prepare_initial,execute_ideal
from ketary._validation import _limit
from research.circuit_rewrite_ladder import stats

def baseline(c,inputs,budget):
    c._require_bound()
    _limit(c.num_qubits,2*len(inputs)+1,budget=budget)
    prepared=tuple(prepare_initial(c.num_qubits,s) for s in inputs)
    return tuple(execute_ideal(c._qc,s,budget) for s in prepared)

def run(seed,reps):
    rng=random.Random(seed);nrng=np.random.default_rng(seed)
    rows=[]
    for n,depth in ((4,0),(4,2),(8,2),(12,1)):
        c=q.Circuit(n)
        for _ in range(depth):
            for i in range(n):c.ry(rng.uniform(-1,1),i)
            for i in range(n-1):c.cx(i,i+1)
        v=nrng.normal(size=1<<n)+1j*nrng.normal(size=1<<n);v/=np.linalg.norm(v)
        snap=q.Result(v)
        inputs=tuple(["0"*n,snap,v,None]*8)
        budget=64*1024**2
        routes={"baseline":lambda:baseline(c,inputs,budget),"candidate":lambda:c.run_many(inputs,max_bytes=budget)}
        expected=routes["baseline"]();times={k:[] for k in routes}
        for _ in range(reps):
            for k in rng.sample(list(routes),len(routes)):
                t=time.perf_counter_ns();actual=routes[k]();dt=(time.perf_counter_ns()-t)/1e6
                for a,b in zip(actual,expected,strict=True):np.testing.assert_array_equal(a._data,b._data)
                times[k].append(dt)
        rows.append(dict(n=n,depth=depth,inputs=len(inputs),seed=seed,paths={k:stats(v) for k,v in times.items()}))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=5);a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps({"scope":"same prepared inputs/outputs and budget; candidate includes public iterable preflight","rows":[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]},indent=2,allow_nan=False))
