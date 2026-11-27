"""Research fixtures shared by independent round-five jobs."""
import json, random, statistics, time
import numpy as np
from qiskit.quantum_info import Pauli, Operator
from benchmark import label
from test_engine import circuit
from round3 import prepare, Prepared
from engine import Obligation, verify, admission, digest

def measure(routes,reps=7):
    rng=random.Random(119);raw={k:[] for k in routes}
    for f in routes.values():
        for _ in range(2):f()
    for _ in range(reps):
        order=list(routes);rng.shuffle(order)
        for k in order:
            t=time.perf_counter_ns();routes[k]();raw[k].append((time.perf_counter_ns()-t)/1e6)
    return {k:{"median_ms":statistics.median(v),"p95_ms":float(np.percentile(v,95)),"samples_ms":v} for k,v in raw.items()}

def bits(p):
    assert int(p.phase) in (0,2)
    return sum(int(x)<<i for i,x in enumerate(p.x)),sum(int(z)<<i for i,z in enumerate(p.z)),int(p.phase)//2

def gates(n,g,seed=119):
    rng=random.Random(seed);out=[]
    for _ in range(g):
        a,b=rng.sample(range(n),2);op=rng.randrange(6)
        out.append((op,a,b if op==5 else 0))
    return out

def semantic(rs):
    return [(r.status,r.circuit_id,r.obligation_id,r.witness) for r in rs]

def output(o):print(json.dumps(o,indent=2,allow_nan=False))
