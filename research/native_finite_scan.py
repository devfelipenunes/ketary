"""Binding finite-scan ablation; no runtime import or dispatch from Ketary."""
import argparse
import ctypes
import json
import math
import os
import platform
import random
import statistics
import subprocess
import tempfile
import time
from pathlib import Path
import numpy as np
import ketary as q
from ketary._adapter import _validate_bound_values

ROOT=Path(__file__).resolve().parent
def compile_kernels(directory):
    sources=ROOT/"native_finite_scan"
    specs={"cpp":(["c++","-O3","-std=c++17","-fPIC","-shared","-fno-fast-math",str(sources/"finite.cpp")],[]),
           "rust":(["rustc","--edition=2021","--crate-type","cdylib","-C","opt-level=3",str(sources/"finite.rs")],[])}
    libraries={}
    for name,(args,_) in specs.items():
        out=Path(directory)/(name+".so")
        subprocess.run(args+["-o",str(out)],check=True,timeout=90)
        lib=ctypes.CDLL(str(out));fn=lib.finite_scan
        fn.argtypes=[np.ctypeslib.ndpointer(dtype=np.float64,ndim=1,flags="C_CONTIGUOUS"),ctypes.c_size_t]
        fn.restype=ctypes.c_int
        libraries[name]=fn
    return libraries

def validate_kernels(kernels):
    cases=[np.array([],dtype=np.float64),np.array([-0.,0.,np.finfo(float).max,np.nextafter(0.,1.)]),
           np.array([1.,np.nan,2.]),np.array([np.inf,1.]),np.array([1.,-np.inf])]
    for size in (1,8,1024):
        for pos in {0,size//2,size-1}:
            for bad in (np.nan,np.inf,-np.inf):
                x=np.ones(size);x[pos]=bad;cases.append(x)
    for x in cases:
        want=all(math.isfinite(float(v)) for v in x)
        assert bool(np.isfinite(x).all())==want
        for fn in kernels.values():assert bool(fn(x,x.size))==want
    return len(cases)

def fixture(n,layers):
    if n not in (4,8,12) or layers not in (4,16,64):raise ValueError("unsupported fixture")
    p=q.Circuit.parameter_vector("p",n)
    c=q.Circuit.symbolic(n)
    for k in range(layers):
        c.ry([x*(k+1)/layers for x in p],range(n)).cx(pairs=q.chain(range(n))).rz(.21,range(n))
    bindings=dict(zip(p,[.1+i*.013 for i in range(n)],strict=True))
    raw=c.to_qiskit()
    bound=raw.assign_parameters(bindings,inplace=False,flat_input=True)
    assert c.bind(bindings).to_qiskit()==bound
    return bound

def evaluate(n,layers,kernels,reps):
    if not 3<=reps<=100:raise ValueError("repetitions must be 3..100")
    raw=fixture(n,layers)
    def collect():
        if raw.parameters:raise ValueError("unbound")
        values=[v for item in raw.data for v in item.params]
        if not all(type(v) is float for v in values):raise TypeError("outside exact-float research subset")
        return values
    values=collect();arr=np.asarray(values,dtype=np.float64)
    def full(scan):
        data=np.asarray(collect(),dtype=np.float64)
        if not scan(data) or not math.isfinite(float(raw.global_phase)):
            raise ValueError("invalid numeric result")
    scans={"numpy":lambda x:bool(np.isfinite(x).all())}
    for name,fn in kernels.items():
        scans[name]=lambda x,fn=fn:bool(fn(x,x.size))
    routes={"current_full":lambda:_validate_bound_values(raw),
            "python_prepacked":lambda:all(math.isfinite(v) for v in values)}
    for name,scan in scans.items():
        routes[name+"_full"]=lambda scan=scan:full(scan)
        routes[name+"_prepacked"]=lambda scan=scan:scan(arr)
    for name,fn in routes.items():
        out=fn()
        if name.endswith("prepacked"):assert out is True
    samples={k:[] for k in routes};orders=[];rng=random.Random(n+layers)
    for i in range(reps+3):
        order=list(routes);rng.shuffle(order)
        if i>=3:orders.append(order)
        for name in order:
            t=time.perf_counter_ns();routes[name]();dt=(time.perf_counter_ns()-t)/1e6
            if i>=3:samples[name].append(dt)
    return dict(n=n,layers=layers,values=len(values),orders=orders,
                variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=20)
    a=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        kernels=compile_kernels(tmp)
        cases=validate_kernels(kernels)
        rows=[evaluate(n,l,kernels,a.repetitions) for n in (4,8,12) for l in (4,16,64)]
    meta=dict(scope="shared runner; scan-only versus full extraction/type check/conversion/phase, not binding assignment or release evidence",python=platform.python_version(),
              cpu=platform.machine(),cpp=subprocess.check_output(["c++","--version"],text=True).splitlines()[0],
              rust=subprocess.check_output(["rustc","--version"],text=True).strip(),fault_cases=cases,
              numpy=np.__version__,simd="compiler may auto-vectorize; no explicit SIMD guarantee",rows=rows)
    for row in rows:print(json.dumps(row,allow_nan=False),flush=True)
    print(json.dumps({k:v for k,v in meta.items() if k!="rows"},allow_nan=False))
    a.output.write_text(json.dumps(meta,indent=2,allow_nan=False))
if __name__=="__main__":main()
