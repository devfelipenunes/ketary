"""Matched research-only chunk profiles and isolated Linux peak RSS.

Compare query outputs, not simulator speed. Do not silently accept changed
top-k ordering: record exact match on every sample and never promote a
candidate with rank disagreements. Marginals and variance allow 1e-9.
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
from importlib.metadata import version
import numpy as np
from ketary._result import _accumulate_pauli_chunks
from research.alpha_chunk_kernels import topk_reference,topk_chunks,marginal_reference,marginal_chunks
from research.circuit_rewrite_ladder import stats

def fixture(n,seed,operation):
    rng=np.random.default_rng(seed)
    state=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    state/=np.linalg.norm(state)
    state.flags.writeable=False
    norm=float(np.vdot(state,state).real)
    wires=(n-1,0,n//2)
    terms=[]
    if operation=="variance":
        labels=set()
        while len(labels)<16:
            labels.add("".join(rng.choice(list("IXYZ"),size=n)))
        terms=[(p,float(rng.uniform(-1,1))) for p in sorted(labels) if p!="I"*n]
    return state,norm,wires,terms

def calculate(operation,state,norm,wires,terms,chunk):
    if operation=="topk":
        return topk_reference(state,32) if not chunk else topk_chunks(state,32,abs(chunk),exact=chunk<0)
    if operation=="marginal":
        return marginal_reference(state,state.size.bit_length()-1,wires,norm) if not chunk else marginal_chunks(state,wires,norm,chunk)
    normalized=state/np.sqrt(norm)
    out=np.zeros_like(normalized)
    _accumulate_pauli_chunks(normalized,out,terms,chunk or min(4096,state.size))
    delta=out-np.vdot(normalized,out)*normalized
    return float(np.vdot(delta,delta).real)

def compare(operation,actual,expected):
    if operation=="topk":
        return {"ordered_match":actual==expected,"max_error":None}
    error=float(np.max(np.abs(np.asarray(actual)-np.asarray(expected))))
    assert error<=1e-9
    return {"ordered_match":None,"max_error":error}

def profile(seed,reps,quick=False):
    rng=random.Random(seed);rows=[]
    configs=((8,"topk"),(8,"marginal"),(8,"variance")) if quick else tuple((n,op) for n in (10,14,18) for op in ("topk","marginal","variance"))
    for n,op in configs:
        state,norm,wires,terms=fixture(n,seed,op)
        baseline=calculate(op,state,norm,wires,terms,0)
        sizes=(0,256,1024,4096,8192) if not quick else (0,64,256)
        sizes=tuple(s for s in sizes if s<=state.size)
        if op=="topk":sizes+=tuple(-s for s in sizes if s>0)
        raw={s:[] for s in sizes};checks={s:[] for s in sizes}
        for _ in range(reps):
            for s in rng.sample(list(sizes),len(sizes)):
                t=time.perf_counter_ns();actual=calculate(op,state,norm,wires,terms,s);dt=(time.perf_counter_ns()-t)/1e6
                raw[s].append(dt);checks[s].append(compare(op,actual,baseline))
                if op=="topk" and s<0:assert actual==baseline
        rows.append(dict(n=n,operation=op,seed=seed,state_bytes=state.nbytes,
            paths={str(s):dict(**stats(raw[s]),checks=checks[s]) for s in sizes}))
    return rows

def worker(n,seed,op,chunk):
    state,norm,wires,terms=fixture(n,seed,op)
    before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t=time.perf_counter_ns();actual=calculate(op,state,norm,wires,terms,chunk)
    elapsed=(time.perf_counter_ns()-t)/1e6
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Compute the oracle only after reading peak RSS for this route.
    expected=calculate(op,state,norm,wires,terms,0)
    return dict(n=n,seed=seed,operation=op,chunk=chunk,before_peak_kib=before,
                peak_kib=peak,elapsed_ms=elapsed,check=compare(op,actual,expected))

def near_ties():
    rows=[]
    for seed in (1101,2202,3303):
        rng=np.random.default_rng(seed)
        state=np.exp(1j*rng.uniform(-np.pi,np.pi,1024))
        state/=np.linalg.norm(state)
        expected=topk_reference(state,32)
        for chunk in (256,1024):
            vector=topk_chunks(state,32,chunk)
            exact=topk_chunks(state,32,chunk,exact=True)
            assert exact==expected
            rows.append(dict(seed=seed,chunk=chunk,vector_ordered_match=vector==expected,
                vector_overlap=len(set(vector)&set(expected)),exact_ordered_match=True))
    return rows

def isolated():
    if platform.system()!="Linux":raise RuntimeError("ru_maxrss unit is KiB on Linux")
    env=dict(os.environ,OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1")
    configurations=[(seed,op,chunk) for seed in (1101,2202,3303)
                    for op in ("topk","marginal","variance") for chunk in (0,1024,8192)]
    configurations.extend((seed,"topk",-1024) for seed in (1101,2202,3303))
    random.Random(1101).shuffle(configurations)
    return [json.loads(subprocess.check_output([sys.executable,"-m","research.alpha_chunk_profile","--worker",
        "--n","18","--seed",str(seed),"--operation",op,"--chunk",str(chunk)],env=env,text=True))
        for seed,op,chunk in configurations]

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=5)
    p.add_argument("--quick",action="store_true");p.add_argument("--rss",action="store_true")
    p.add_argument("--worker",action="store_true");p.add_argument("--n",type=int,default=18,choices=(10,14,18))
    p.add_argument("--seed",type=int,default=1101);p.add_argument("--operation",choices=("topk","marginal","variance"),default="topk")
    p.add_argument("--chunk",type=int,default=0,choices=(0,256,1024,4096,8192,-1024))
    a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    result=worker(a.n,a.seed,a.operation,a.chunk) if a.worker else dict(
        scope="research kernels; baseline chunk 0 means existing route; negative topk chunk uses exact scalar scoring; peak RSS lifetime high-water, not incremental memory",
        python=platform.python_version(),numpy=version("numpy"),qiskit=version("qiskit"),
        rows=[r for seed in (1101,2202,3303) for r in profile(seed,a.reps,a.quick)],
        near_ties=near_ties(),isolated_rss=isolated() if a.rss else [])
    print(json.dumps(result,indent=2,allow_nan=False))
