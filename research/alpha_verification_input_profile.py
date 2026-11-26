"""Old/new input preparation for independent selected product-state runs."""
import argparse
import json
import random
import time
import numpy as np
import ketary as q
from qiskit.quantum_info import Statevector
from ketary._verification import _outputs
from research.circuit_rewrite_ladder import stats

def run(seed,reps):
    rng=random.Random(seed)
    rows=[]
    for n,depth in ((4,0),(4,2),(8,2),(12,1)):
        a=q.Circuit(n)
        for _ in range(depth):
            for i in range(n):a.ry(rng.uniform(-1,1),i)
        b=a.copy().rz(.17,n-1)
        labels=tuple("".join(rng.choice("01+-rl") for _ in range(n)) for _ in range(16))
        budget=64*1024**2
        def old():
            out=[]
            for label in labels:
                v=Statevector.from_label(label).data
                out.append((a.run(initial_state=v,max_bytes=budget),b.run(initial_state=v,max_bytes=budget)))
            return tuple(out)
        def new():return tuple(_outputs(a,b,label,budget) for label in labels)
        routes={"baseline":old,"candidate":new};expected=old();timings={k:[] for k in routes}
        for _ in range(reps):
            for k in rng.sample(list(routes),len(routes)):
                t=time.perf_counter_ns();actual=routes[k]();dt=(time.perf_counter_ns()-t)/1e6
                for pair,ref in zip(actual,expected,strict=True):
                    for x,y in zip(pair,ref,strict=True):np.testing.assert_array_equal(x._data,y._data)
                timings[k].append(dt)
        rows.append(dict(n=n,depth=depth,seed=seed,inputs=len(labels),paths={k:stats(v) for k,v in timings.items()}))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=5);a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps({"scope":"matched output preparation/evolution; candidate also validates label; no changed witness guarantees","rows":[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]},indent=2,allow_nan=False))
