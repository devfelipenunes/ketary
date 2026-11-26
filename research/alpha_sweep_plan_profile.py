"""Paired internal sweep batch benchmark: identical ownership and outputs."""
import argparse
import json
import random
import time
import numpy as np
import ketary as q
from qiskit.quantum_info import Operator
from research.circuit_rewrite_ladder import stats

def build(n,depth,dense):
    a,b=q.Circuit.parameter_vector("a",2)
    c=q.Circuit.symbolic(n)
    for _ in range(depth):
        if dense:c.ry(a+b,range(n)).rz(b,range(n))
        else:c.h(range(n)).cx(0,n-1)
    c.ry(a,0).rz(b,n-1)
    raw=c.to_qiskit();raw.global_phase=.2*a-.4*b
    return q.Circuit.from_symbolic(raw)

def run(seed,reps):
    rng=random.Random(seed)
    out=[]
    for n,depth in ((4,1),(4,8),(8,8),(12,8)):
        for dense in (False,True):
            c=build(n,depth,dense)
            keys=tuple(reversed(c.parameters))
            rows=tuple(tuple((p.name,rng.uniform(-1,1)) for p in keys) for _ in range(32))
            def baseline():
                return tuple(c._bind_numeric(dict(zip(keys,(v for _,v in row),strict=True))) for row in rows)
            def candidate():
                return c._bind_sweep_rows(rows,keys)
            routes={"baseline":baseline,"candidate":candidate}
            expected=tuple(p.to_qiskit() for p in baseline())
            before=c.to_qiskit()
            timings={k:[] for k in routes}
            for _ in range(reps):
                for name in rng.sample(list(routes),len(routes)):
                    t=time.perf_counter_ns();batch=routes[name]();dt=(time.perf_counter_ns()-t)/1e6
                    assert tuple(p.to_qiskit() for p in batch)==expected
                    timings[name].append(dt)
            if n==4:
                for got,ref in zip(candidate(),expected,strict=True):
                    np.testing.assert_allclose(Operator(got.to_qiskit()).data,Operator(ref).data,atol=1e-9,rtol=0)
            assert c.to_qiskit()==before
            out.append(dict(n=n,depth=depth,dense=dense,operations=len(before.data),seed=seed,rows=32,
                paths={k:stats(v) for k,v in timings.items()}))
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=9);a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps({"scope":"matched private batch after preflight; same retained bound circuits, excludes export and execution", "rows":[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]},indent=2,allow_nan=False))
