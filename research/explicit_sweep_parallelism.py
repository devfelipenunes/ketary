"""Explicit bounded sweep concurrency study, not a new SDK execution mode."""
import argparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json
import multiprocessing
import os
import random
import statistics
import time
from pathlib import Path
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

def workload(n,count):
    if n not in (6,10,14) or count not in (4,16):
        raise ValueError("unsupported bounded workload")
    p=q.Circuit.parameter_vector("p",n)
    c=q.Circuit.symbolic(n)
    for k in range(4):
        c.ry([v*(k+1)/4 for v in p],range(n))
        c.cx(pairs=q.chain(range(n)))
    rng=np.random.default_rng(812+n+count)
    rows=rng.uniform(-1,1,(count,n)).tolist()
    # Independent, fully bound native circuits per task, not a mutable shared template.
    circuits=tuple(c.bind(row) for row in rows)
    payloads=tuple(x.to_json() for x in circuits)
    raw=c.to_qiskit()
    native=[Statevector.from_instruction(raw.assign_parameters(dict(zip(p,row,strict=True)))).data for row in rows]
    return circuits,payloads,native

def thread_task(c):
    return c.run().math.statevector()

def process_task(payload):
    return q.Circuit.from_json(payload).run().math.statevector()

def evaluate(n,count,reps):
    if not 3<=reps<=20:raise ValueError("repetitions must be 3..20")
    circuits,payloads,wanted=workload(n,count)
    # Pool startup and teardown counted in every sample, no implicit persistence.
    def serial():
        return tuple(map(thread_task,circuits))
    def threads():
        with ThreadPoolExecutor(max_workers=2) as pool:
            return tuple(pool.map(thread_task,circuits))
    def processes():
        with ProcessPoolExecutor(max_workers=2,mp_context=multiprocessing.get_context("spawn")) as pool:
            return tuple(pool.map(process_task,payloads))
    routes={"serial":serial,"threads2":threads,"processes2":processes}
    errors={}
    for name,fn in routes.items():
        got=fn()
        np.testing.assert_allclose(got,wanted,atol=1e-9,rtol=0)
        errors[name]=float(np.max(np.abs(np.asarray(got)-wanted)))
    samples={k:[] for k in routes};orders=[];rng=random.Random(n+count)
    for i in range(reps):
        order=list(routes);rng.shuffle(order);orders.append(order)
        for name in order:
            t=time.perf_counter_ns();out=routes[name]();dt=(time.perf_counter_ns()-t)/1e6
            samples[name].append(dt);del out
    assert tuple(x.to_json() for x in circuits)==payloads
    return dict(n=n,count=count,workers=2,errors=errors,orders=orders,
                retained_output_bytes=count*16*(1<<n),
                variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=5)
    a=p.parse_args()
    rows=[]
    for n in (6,10,14):
        for count in (4,16):
            row=evaluate(n,count,a.repetitions);rows.append(row);print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(scope="explicit independent tasks, cold pools including spawn/replay/transport, shared CI, no concurrency or aggregate RSS guarantee",
        threads={k:os.environ.get(k) for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS")},rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
