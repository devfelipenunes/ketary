"""Diagnose binding overhead; measure a candidate, never skip validation.

Run python -m research.alpha_binding_profile --reps 9.
All routes retain the same 32 bound circuits and validate equality.
Shared CI is diagnostic; no public API or execution change.
"""
import argparse
import json
import platform
import random
import time
from importlib.metadata import version
import numpy as np
import ketary as q
from ketary._adapter import _validate_bound_values
from qiskit.quantum_info import Operator
from research.circuit_rewrite_ladder import stats

def template(n,depth):
    a,b=q.Circuit.parameter_vector("a",2)
    circuit=q.Circuit.symbolic(n)
    for _ in range(depth):
        circuit.ry(a,range(n)).rz(a+b,range(n))
    circuit.evolve(.4*q.I(),time=b)
    return circuit

def run(seed,reps):
    rng=random.Random(seed)
    out=[]
    for n,depth in ((4,1),(4,8),(8,8),(12,8)):
        c=template(n,depth)
        native=c.to_qiskit()
        params=tuple(native.parameters)
        values=tuple(tuple(rng.uniform(-1,1) for _ in params) for _ in range(32))
        expected=tuple(native.assign_parameters(dict(zip(params,row,strict=True))) for row in values)
        before=c.to_qiskit()
        def sdk():
            plan=c.sweep_rows(values)
            return tuple(payload.to_qiskit() for payload in plan._payloads)
        def dictionary():
            results=tuple(native.assign_parameters(dict(zip(params,row,strict=True)),flat_input=True) for row in values)
            for v in results:_validate_bound_values(v)
            return results
        def ordered():
            results=tuple(native.assign_parameters(row) for row in values)
            for v in results:_validate_bound_values(v)
            return results
        routes={"sweep_plus_export":sdk,"dict_validated":dictionary,"ordered_validated":ordered}
        timing={name:[] for name in routes}
        for _ in range(reps):
            for name in rng.sample(list(routes),len(routes)):
                start=time.perf_counter_ns();actual=routes[name]();end=time.perf_counter_ns()
                assert actual==expected
                timing[name].append((end-start)/1e6)
        if n==4:
            for actual,ref in zip(ordered(),expected,strict=True):
                np.testing.assert_allclose(Operator(actual).data,Operator(ref).data,atol=1e-9,rtol=0)
        assert c.to_qiskit()==before
        stages={"mapping":[],"native":[],"validate":[],"wrapper":[]}
        for _ in range(reps):
            t0=time.perf_counter_ns()
            mappings=tuple(dict(zip(params,row,strict=True)) for row in values)
            t1=time.perf_counter_ns()
            raw=tuple(native.assign_parameters(mapping,flat_input=True) for mapping in mappings)
            t2=time.perf_counter_ns()
            for bound in raw:_validate_bound_values(bound)
            t3=time.perf_counter_ns()
            wrapped=[]
            for bound in raw:
                obj=q.Circuit.__new__(q.Circuit);obj._qc=bound;wrapped.append(obj)
            t4=time.perf_counter_ns()
            assert raw==expected and len(wrapped)==32
            for key,a,b in zip(stages,(t0,t1,t2,t3),(t1,t2,t3,t4),strict=True):
                stages[key].append((b-a)/1e6)
        out.append(dict(n=n,depth=depth,operations=len(native.data),rows=32,seed=seed,
            paths={k:stats(v) for k,v in timing.items()},
            stages={k:stats(v) for k,v in stages.items()},
            scope="sweep includes defensive export; candidate native paths exclude export; compare dict/ordered directly only"))
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=9);a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps(dict(python=platform.python_version(),qiskit=version("qiskit"),
      rows=[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]),indent=2,allow_nan=False))
