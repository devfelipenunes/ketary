"""Narrow full-width string query attribution; no SDK implementation change."""
import argparse
import json
import math
import random
import statistics
import time
from pathlib import Path

import numpy as np
import ketary as q
from qiskit.quantum_info import Pauli, Statevector


def _query(snapshot,labels,*,reuse):
    """Same bounded validated distinct canonical labels in both research paths."""
    if not isinstance(labels,tuple) or not 1<=len(labels)<=32:
        raise ValueError("expected tuple of 1..32 labels")
    n=snapshot.num_qubits
    if any(type(label) is not str or len(label)!=n or set(label)-set("IXYZ")
           for label in labels) or len(set(labels))!=len(labels):
        raise ValueError("expected distinct canonical labels")
    data=snapshot._data
    norm=snapshot._norm_sq
    if len(labels)*data.size>64*1024**2:
        raise q.ResourceLimit("grouped expectation work exceeds budget")
    state=Statevector(data) if reuse else None
    out=[]
    for label in labels:
        handle=state if reuse else Statevector(data)
        value=complex(handle.expectation_value(Pauli(label)))
        if not math.isfinite(value.real) or not math.isfinite(value.imag) or abs(value.imag)>1e-9:
            raise ArithmeticError("invalid Hermitian Pauli expectation")
        out.append(float(np.clip(value.real/norm,-1,1)))
    return tuple(out)


def independent(data,label):
    """Scalar Pauli bit action, not native expectation or dense allocation."""
    total=0j
    for j,amplitude in enumerate(data):
        target=j
        phase=1+0j
        for wire,axis in enumerate(reversed(label)):
            bit=(j>>wire)&1
            if axis in "XY":
                target^=1<<wire
            if axis=="Y":
                phase*=1j*(-1 if bit else 1)
            elif axis=="Z":
                phase*=(-1 if bit else 1)
        total+=complex(data[target]).conjugate()*phase*complex(amplitude)
    return total.real/float(np.vdot(data,data).real)


def workload(n,count,seed):
    if n not in (4,8,12) or count not in (1,8,32):
        raise ValueError("unsupported workload")
    rng=np.random.default_rng(seed)
    data=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    data/=np.linalg.norm(data)
    labels=[]
    while len(labels)<count:
        label="".join(rng.choice(list("IXYZ"),size=n))
        if label not in labels:
            labels.append(label)
    return data,tuple(labels)


def evaluate(n,count,seed,repetitions):
    if not 3<=repetitions<=100:
        raise ValueError("repetitions must be 3..100")
    data,labels=workload(n,count,seed)
    snapshot=q.Result(data)
    original=snapshot.math.statevector()
    expected=tuple(independent(data,label) for label in labels)
    # Emulate prior public grouped path for this same canonical-label subset:
    # validate all labels, sort, call scalar expectation once per unique label,
    # and restore the caller order. No general weighted-input speedup claim.
    def previous_grouped():
        if len(labels)*snapshot._data.size>64*1024**2:
            raise q.ResourceLimit("grouped expectation work exceeds budget")
        if any(len(label)!=n or set(label)-set("IXYZ") for label in labels):
            raise ValueError("invalid labels")
        cache={label:snapshot.math.expectation(label) for label in sorted(labels)}
        return tuple(math.fsum((cache[label],)) for label in labels)
    variants={"previous_grouped_subset":previous_grouped,"sdk":lambda:snapshot.math.expectations(labels),
              "fresh_native":lambda:_query(snapshot,labels,reuse=False),
              "reused_native":lambda:_query(snapshot,labels,reuse=True)}
    errors={}
    for name,fn in variants.items():
        result=fn()
        np.testing.assert_allclose(result,expected,atol=1e-9,rtol=0)
        errors[name]=float(np.max(np.abs(np.array(result)-expected)))
    samples={name:[] for name in variants}
    order=[]
    rand=random.Random(seed)
    for _ in range(repetitions):
        names=list(variants)
        rand.shuffle(names)
        order.append(names)
        for name in names:
            t=time.perf_counter_ns()
            variants[name]()
            samples[name].append((time.perf_counter_ns()-t)/1e6)
    np.testing.assert_array_equal(snapshot.math.statevector(),original)
    return dict(n=n,labels=count,seed=seed,errors=errors,order=order,
                scope="diagnostic shared-runner, distinct canonical string labels only",
                variants={name:dict(raw_ms=values,p50_ms=statistics.median(values),
                    p95_ms=float(np.quantile(values,.95))) for name,values in samples.items()})


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--repetitions",type=int,default=15)
    parser.add_argument("--seed",type=int,default=1101)
    a=parser.parse_args()
    rows=[evaluate(n,k,a.seed,a.repetitions) for n in (4,8,12) for k in (1,8,32)]
    for row in rows:
        print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(rows,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
