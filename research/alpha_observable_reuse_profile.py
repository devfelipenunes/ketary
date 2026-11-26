"""Matched old/new weighted expectation on identical immutable snapshots."""
import argparse
import itertools
import json
import math
import random
import time
import numpy as np
import ketary as q
from ketary._validation import _real
from research.circuit_rewrite_ladder import stats

def run(seed,reps):
    rng=random.Random(seed);nrng=np.random.default_rng(seed)
    rows=[]
    for n,count in ((4,1),(4,32),(4,256),(8,64),(12,64)):
        labels=["".join(p) for p in itertools.product("IXYZ",repeat=min(n,4))]
        terms={p.rjust(n,"I"):rng.uniform(-1,1) for p in rng.sample(labels,count)}
        v=nrng.normal(size=1<<n)+1j*nrng.normal(size=1<<n);v/=np.linalg.norm(v)
        r=q.Result(v);m=r.math
        def baseline():
            return math.fsum(_real(coefficient)*m.expectation(label) for label,coefficient in terms.items())
        def candidate():
            return m.observable(terms)
        routes={"baseline":baseline,"candidate":candidate}
        expected=baseline();timing={k:[] for k in routes}
        for _ in range(reps):
            for key in rng.sample(list(routes),len(routes)):
                start=time.perf_counter_ns();value=routes[key]();dt=(time.perf_counter_ns()-start)/1e6
                assert value==expected
                timing[key].append(dt)
        rows.append(dict(n=n,terms=count,seed=seed,paths={k:stats(v) for k,v in timing.items()}))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=9);a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps({"scope":"identical per-term expectation and fsum, excludes construction and state evolution","rows":[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]},indent=2,allow_nan=False))
