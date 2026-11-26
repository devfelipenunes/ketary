"""Research only: bounded finite scans and byte admission, no public API.

Keep complex128 storage, complete norm calculation, strict UTF-8 handling,
and original ownership. Do not adopt approximate norms or lossy compression.
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
from research.circuit_rewrite_ladder import stats

def finite_full(a):
    return bool(np.isfinite(a).all())

def finite_chunked(a,chunk=8192):
    return all(np.isfinite(a[i:i+chunk]).all() for i in range(0,len(a),chunk))

def finite_reuse(a,chunk=8192):
    scratch=np.empty(min(chunk,a.size),dtype=np.bool_)
    for i in range(0,len(a),chunk):
        block=a[i:i+chunk]
        view=scratch[:len(block)]
        np.isfinite(block,out=view)
        if not view.all():return False
    return True

def norm_and_valid(a,check):
    # Preserve actual SDK norm reduction and finite/tolerance policy.
    import math
    norm=float(np.vdot(a,a).real)
    return norm,check(a) and math.isclose(norm,1,rel_tol=0,abs_tol=1e-9)

def byte_full(text):
    return len(text.encode("utf-8"))

def byte_ascii(text):
    return len(text) if text.isascii() else len(text.encode("utf-8"))

def state_fixture(n,seed):
    rng=np.random.default_rng(seed)
    a=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    a/=np.sqrt(np.vdot(a,a).real)
    a.flags.writeable=False
    return a

def run(seed,reps,quick=False):
    rng=random.Random(seed);rows=[]
    for n in ((10,) if quick else (10,14,18,20)):
        a=state_fixture(n,seed)
        before=a.copy()
        paths={"full":lambda:norm_and_valid(a,finite_full),
               "chunk":lambda:norm_and_valid(a,finite_chunked),
               "reuse":lambda:norm_and_valid(a,finite_reuse)}
        expected=paths["full"]()
        timing={k:[] for k in paths}
        for _ in range(reps):
            for k in rng.sample(list(paths),len(paths)):
                t=time.perf_counter_ns();value=paths[k]();dt=(time.perf_counter_ns()-t)/1e6
                assert value==expected
                timing[k].append(dt)
        assert np.array_equal(a,before) and not a.flags.writeable
        rows.append(dict(kind="snapshot_validation",n=n,seed=seed,payload_bytes=a.nbytes,
                         boolean_scratch_upper_bound={"full":a.size,"chunk":min(8192,a.size),"reuse":min(8192,a.size)},
                         paths={k:stats(v) for k,v in timing.items()}))
    for size in ((4096,) if quick else (4096,65536,1048576)):
        for char in ("a","é","🧪"):
            payload=char*size
            paths={"full":lambda:byte_full(payload),"ascii":lambda:byte_ascii(payload)}
            expected=paths["full"]();timing={k:[] for k in paths}
            for _ in range(reps):
                for k in rng.sample(list(paths),len(paths)):
                    t=time.perf_counter_ns();value=paths[k]();dt=(time.perf_counter_ns()-t)/1e6
                    assert value==expected;timing[k].append(dt)
            rows.append(dict(kind="utf8_length_only",characters=size,utf8_bytes=expected,
                             ascii=payload.isascii(),codepoint=ord(char),seed=seed,
                             paths={k:stats(v) for k,v in timing.items()}))
    return rows

def worker(n,seed,route):
    a=state_fixture(n,seed)
    check={"full":finite_full,"chunk":finite_chunked,"reuse":finite_reuse}[route]
    before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t=time.perf_counter_ns();value=norm_and_valid(a,check);dt=(time.perf_counter_ns()-t)/1e6
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert value==norm_and_valid(a,finite_full)
    return dict(n=n,seed=seed,route=route,elapsed_ms=dt,baseline_peak_kib=before,
                peak_kib=peak,payload_bytes=a.nbytes)

def isolated():
    if platform.system()!="Linux":raise RuntimeError("Linux KiB required")
    env=dict(os.environ,OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1")
    configs=[(n,s,r) for n in (18,20) for s in (1101,2202,3303) for r in ("full","chunk","reuse")]
    random.Random(1101).shuffle(configs)
    return [json.loads(subprocess.check_output([sys.executable,"-m","research.alpha_buffer_normalization",
            "--worker",r,"--n",str(n),"--seed",str(s)],env=env,text=True)) for n,s,r in configs]

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--reps",type=int,default=5);p.add_argument("--quick",action="store_true")
    p.add_argument("--rss",action="store_true");p.add_argument("--worker",choices=("full","chunk","reuse"))
    p.add_argument("--n",type=int,choices=(18,20),default=20);p.add_argument("--seed",type=int,default=1101)
    a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps(worker(a.n,a.seed,a.worker) if a.worker else dict(
        scope="research only; RSS process lifetime high water; not total allocation count",
        python=platform.python_version(),numpy=version("numpy"),
        rows=[r for s in (1101,2202,3303) for r in run(s,a.reps,a.quick)],
        isolated_rss=isolated() if a.rss else []),indent=2,allow_nan=False))
