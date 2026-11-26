"""Paired scope-specific verification; no comparison of unequal guarantees."""
import json
import random
import time
import numpy as np
import ketary as q
from qiskit.quantum_info import Operator
from research.circuit_rewrite_ladder import stats

def run(seed,reps=5):
    rng=random.Random(seed);rows=[]
    for n in (2,4,6):
        a=q.Circuit(n)
        for _ in range(3):
            for wire in range(n):a.ry(rng.uniform(-1,1),wire)
            for wire in range(n-1):a.cx(wire,wire+1)
        for different in (False,True):
            b=a.copy()
            if different:b.z(n-1)
            delta=Operator(a.to_qiskit()).data-Operator(b.to_qiskit()).data
            expected="FAIL" if float(np.max(abs(delta)))>1e-9 else "PASS"
            routes={"dense":lambda:a.test.metrics(b),
                    "selected_then_dense":lambda:a.test.compare(b,inputs=["0"*n,"+"*n],complete=True)}
            # The two modes have different evidence payloads. Report separately,
            # only their final verdict is compared with the full operator oracle.
            timing={k:[] for k in routes}
            for _ in range(reps):
                for k in rng.sample(list(routes),len(routes)):
                    t=time.perf_counter_ns();r=routes[k]();dt=(time.perf_counter_ns()-t)/1e6
                    assert r.status==expected;timing[k].append(dt)
            rows.append(dict(n=n,seed=seed,different=different,expected=expected,
                             paths={k:stats(v) for k,v in timing.items()}))
    return rows

if __name__=="__main__":
    print(json.dumps({"scope":"distinct evidence paths; no equivalent-overhead or QCEC speed claim",
       "rows":[r for seed in (1101,2202,3303) for r in run(seed)]},indent=2,allow_nan=False))
