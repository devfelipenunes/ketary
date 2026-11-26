"""Linux per-process sweep benchmark, matching output and retaining all samples.

Run: python -m research.alpha_sweep_rss --reps 5
Use the dedicated-host protocol for controlled claims; shared CI is diagnostic.
Peak RSS is process lifetime high water, not an incremental allocation counter.
"""
import argparse
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
import numpy as np
import ketary as q
from qiskit import QuantumCircuit, __version__ as qiskit_version
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector

def rss_kib():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

def worker(route, n, seed):
    values = np.random.default_rng(seed).uniform(-2., 2., 32)
    before = rss_kib()
    start = time.perf_counter_ns()
    if route == "ketary":
        p = q.Circuit.parameter("p")
        c = q.Circuit.symbolic(n).ry(p, range(n))
        built = time.perf_counter_ns()
        bound = c.sweep_rows((float(v),) for v in values)
        prepared = time.perf_counter_ns()
        results = bound.run()
        executed = time.perf_counter_ns()
        states = tuple(r.math.statevector() for r in results)
    else:
        p = Parameter("p")
        c = QuantumCircuit(n)
        c.ry(p, range(n))
        built = time.perf_counter_ns()
        bound = tuple(c.assign_parameters({p: float(v)}) for v in values)
        prepared = time.perf_counter_ns()
        results = tuple(Statevector.from_instruction(x) for x in bound)
        executed = time.perf_counter_ns()
        states = tuple(r.data.copy() for r in results)
    read = time.perf_counter_ns()
    peak = rss_kib()
    # Validate complete vectors, not just a scalar checksum, after timing.
    for state, v in zip(states, values, strict=True):
        single = np.array([np.cos(v/2), np.sin(v/2)])
        expected = np.array([1.])
        for _ in range(n):
            expected = np.kron(expected, single)
        np.testing.assert_allclose(state, expected, atol=1e-9, rtol=0)
    return dict(route=route, n=n, seed=seed, before_peak_kib=before, peak_kib=peak,
                stage_ms=[(b-a)/1e6 for a,b in zip((start,built,prepared,executed),(built,prepared,executed,read),strict=True)],
                output_bytes=sum(s.nbytes for s in states))

def summarize(samples):
    return dict(p50=float(np.median(samples)),p95=float(np.percentile(samples,95)),raw=samples)

def run(reps):
    if platform.system() != "Linux":
        raise RuntimeError("ru_maxrss units are Linux KiB for this protocol")
    rng = random.Random(1101)
    rows = []
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    for n in (4,8,12):
        for seed in (1101,2202,3303):
            samples = {"ketary":[], "qiskit":[]}
            for _ in range(reps):
                for route in rng.sample(list(samples),2):
                    raw = subprocess.check_output([sys.executable,"-m","research.alpha_sweep_rss","--worker",route,"--n",str(n),"--seed",str(seed)],env=env,text=True)
                    samples[route].append(json.loads(raw))
            rows.append(dict(n=n, seed=seed, routes={route:{
                "raw":values,
                "peak_kib":summarize([v["peak_kib"] for v in values]),
                "stage_ms":[summarize([v["stage_ms"][i] for v in values]) for i in range(4)]
            } for route,values in samples.items()}))
    return dict(scope="authored diagnostic; no dedicated-host or speedup claim",stage_order=["build","bind","execute","read"],python=sys.version,qiskit=qiskit_version,host=platform.platform(),cpu_affinity=sorted(os.sched_getaffinity(0)),rows=rows)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--worker",choices=["ketary","qiskit"])
    p.add_argument("--n",type=int,choices=[4,8,12],default=4)
    p.add_argument("--seed",type=int,default=1101)
    p.add_argument("--reps",type=int,default=5)
    a=p.parse_args()
    if a.reps<1:
        p.error("reps must be positive")
    print(json.dumps(worker(a.worker,a.n,a.seed) if a.worker else run(a.reps),indent=2,allow_nan=False))
