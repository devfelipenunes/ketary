"""Paired diagnostic benchmark; not a release gate on shared CI hardware."""
import argparse
import json
import os
import platform
import random
import resource
import statistics
import subprocess
import sys
import time
import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import ketary as q

def workload(n, count):
    rng=random.Random(20261125+n+count)
    ops=[]
    for _ in range(count):
        name=rng.choice(("h","x","z","cx","swap"))
        wires=tuple(rng.sample(range(n),2 if name in ("cx","swap") else 1))
        ops.append((name,wires))
    return ops

def build(n, ops, variant):
    c=QuantumCircuit(n) if variant=="native" else q.Circuit(n)
    gates=c if variant=="native" else c.gates
    for name,wires in ops:
        getattr(gates,name)(*wires)
    return c

def execute(c,variant):
    # Both return an independent complex128 vector. Ketary additionally validates
    # normalization and preserves an independent Result; report this extra work.
    return Statevector.from_instruction(c).data.copy() if variant=="native" else c.run().math.statevector()

def summarize(values):
    return {"median_ms":statistics.median(values),"p95_ms":float(np.percentile(values,95)),"raw_ms":values}

def paired(native,sdk,reps):
    functions={"native":native,"sdk":sdk}
    samples={k:[] for k in functions}
    rng=random.Random(42)
    for i in range(reps+3):
        order=list(functions); rng.shuffle(order)
        for label in order:
            t=time.perf_counter_ns(); result=functions[label](); elapsed=(time.perf_counter_ns()-t)/1e6
            del result
            if i>=3: samples[label].append(elapsed)
    a,b=(summarize(samples[k]) for k in ("native","sdk"))
    return {"native":a,"sdk":b,"overhead_percent":100*(b["median_ms"]/a["median_ms"]-1),"delta_ms":b["median_ms"]-a["median_ms"]}

def memory_kib():
    # Linux /proc VmHWM is the process image high-water mark, avoiding
    # ru_maxrss inheritance from the benchmark coordinator across fork/exec.
    if sys.platform.startswith("linux"):
        with open("/proc/self/status",encoding="utf-8") as f:
            fields={line.split(":",1)[0]:line.split(":",1)[1].strip() for line in f if ":" in line}
        return {"current_kib":int(fields["VmRSS"].split()[0]),"peak_kib":int(fields["VmHWM"].split()[0]),"source":"procfs"}
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"current_kib":None,"peak_kib":peak/1024 if sys.platform=="darwin" else peak,"source":"getrusage"}

def rss_worker(variant):
    n=20; ops=[("h",(0,)),("cx",(0,n-1)),("z",(n-1,))]
    c=build(n,ops,variant); before=memory_kib()
    state=execute(c,variant)
    after=memory_kib()
    assert np.count_nonzero(abs(state)>1e-12)==2
    assert np.isclose(np.linalg.norm(state),1)
    return {"variant":variant,"n":n,"gates":len(ops),"before":before,"after":after,"payload_bytes":state.nbytes}

def main(reps):
    data={"python":sys.version,"platform":platform.platform(),"qiskit":qiskit.__version__,"numpy":np.__version__,"cpu":platform.processor(),"repetitions":reps,"cases":[],"rss":[]}
    for n,count in [(8,1000),(8,10000)]:
        ops=workload(n,count)
        native=build(n,ops,"native"); sdk=build(n,ops,"sdk")
        assert native==sdk.to_qiskit()
        result=paired(lambda:build(n,ops,"native"),lambda:build(n,ops,"sdk"),reps)
        data["cases"].append({"operation":"build","n":n,"gates":count,**result})
    for n,count in [(8,128),(12,128),(16,64)]:
        ops=workload(n,count)
        native=build(n,ops,"native"); sdk=build(n,ops,"sdk")
        np.testing.assert_allclose(execute(native,"native"),execute(sdk,"sdk"),atol=1e-9,rtol=0)
        result=paired(lambda:execute(native,"native"),lambda:execute(sdk,"sdk"),reps)
        data["cases"].append({"operation":"statevector","n":n,"gates":count,**result})
    variants=["native","sdk"]*3; random.Random(42).shuffle(variants)
    for variant in variants:
        raw=subprocess.check_output([sys.executable,__file__,"--rss-worker",variant],text=True)
        data["rss"].append(json.loads(raw))
    return data

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--repetitions",type=int,default=20)
    parser.add_argument("--rss-worker",choices=["native","sdk"])
    args=parser.parse_args()
    if args.rss_worker: result=rss_worker(args.rss_worker)
    else:
        if args.repetitions<20: parser.error("at least 20 repetitions")
        result=main(args.repetitions)
    print(json.dumps(result,indent=2))
