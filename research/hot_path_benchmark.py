"""Same-runner hot-path timings. Uses identical script on both revisions."""
import argparse
import json
import os
import resource
import statistics
import time
import random
import numpy as np
import ketary as q
from qiskit.quantum_info import Statevector

def run(reps,seed):
    rng=random.Random(seed)
    results=[]
    def add(name,meta,fn,oracle):
        expected=oracle()
        actual=fn()
        np.testing.assert_allclose(actual,expected,atol=1e-9,rtol=0)
        samples=[]
        for i in range(reps+3):
            start=time.perf_counter_ns()
            result=fn()
            elapsed=(time.perf_counter_ns()-start)/1e6
            del result
            if i>=3: samples.append(elapsed)
        row={"case":name,**meta,"median_ms":statistics.median(samples),
             "p95_ms":float(np.percentile(samples,95)),"raw_ms":samples}
        results.append(row)
        print(json.dumps({k:v for k,v in row.items() if k!="raw_ms"}),flush=True)
    for n in (8,16,20,22):
        data=np.random.default_rng(seed+n).normal(size=1<<n)+1j*np.random.default_rng(seed+n+1).normal(size=1<<n)
        data/=np.linalg.norm(data)
        snapshot=q.Result(data)
        c=q.Circuit(n).h(0).cx(0,n-1)
        expected=Statevector(data).evolve(c.to_qiskit()).data
        add("snapshot_evolve",{"n":n},lambda:c.run(initial_state=snapshot).math.statevector(),lambda:expected)
        empty=q.Circuit(n)
        add("snapshot_empty",{"n":n},lambda:empty.run(initial_state=snapshot).math.statevector(),lambda:data)
    for n,depth in ((4,2),(8,4),(32,8)):
        c=q.ansatz(n,rotations=("ry","rz"),reps=depth)
        params=c.parameters
        values=[rng.uniform(-1,1) for _ in params]
        native=c.to_qiskit()
        expected=native.assign_parameters(values)
        def bind():
            out=c.bind(values).to_qiskit()
            if out!=expected: raise AssertionError("native circuit mismatch")
            return len(out.data)
        add("binding",{"n":n,"parameters":len(params)},bind,lambda:len(expected.data))
    for n,count in ((4,8),(6,32)):
        c=q.ansatz(n,reps=2)
        rows=np.random.default_rng(seed).uniform(-1,1,size=(count,len(c.parameters)))
        native=c.to_qiskit()
        expected=np.array([Statevector.from_instruction(native.assign_parameters(row)).data for row in rows])
        add("sweep",{"n":n,"rows":count},lambda:np.array([r.math.statevector() for r in c.sweep_rows(rows).run()]),lambda:expected)
        plan=c.sweep_rows(rows)
        add("sweep_run_only",{"n":n,"rows":count},lambda:np.array([r.math.statevector() for r in plan.run()]),lambda:expected)
    return {"seed":seed,"repetitions":reps,"max_rss_kib_linux":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"cases":results}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--seed",type=int,default=1101)
    p.add_argument("--repetitions",type=int,default=30)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    if not 3<=a.repetitions<=100: p.error("3..100 repetitions")
    with open(a.output,"w") as f: json.dump(run(a.repetitions,a.seed),f,indent=2,allow_nan=False)
