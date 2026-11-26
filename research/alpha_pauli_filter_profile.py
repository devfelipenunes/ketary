"""Exact old-versus-new Pauli algebra profiling. Same coefficient aggregation."""
import argparse
import itertools
import json
import random
import time
import ketary as q
from ketary._observable import Observable,_pauli_product,_sum_complex
from ketary._validation import _real,ResourceLimit
from research.circuit_rewrite_ladder import stats

def baseline(left,right,*,mode="product"):
    if not isinstance(right,Observable):
        raise TypeError("expected Observable")
    n=max(left.num_qubits,right.num_qubits)
    a,b=left.to_dict(n),right.to_dict(n)
    if len(a)*len(b)>4096:
        raise ResourceLimit("Pauli product exceeds 4096 term pairs")
    table={("X","Y"):("Z",1j),("Y","Z"):("X",1j),("Z","X"):("Y",1j),
           ("Y","X"):("Z",-1j),("Z","Y"):("X",-1j),("X","Z"):("Y",-1j)}
    out={}
    for p,x in a.items():
        for q,y in b.items():
            phase=1+0j
            label=[]
            for u,v in zip(p,q,strict=True):
                if u=="I":label.append(v)
                elif v=="I":label.append(u)
                elif u==v:label.append("I")
                else:
                    axis,factor=table[u,v]
                    label.append(axis)
                    phase*=factor
            if mode=="commutator":
                phase=2j*phase.imag
            elif mode=="anticommutator":
                phase=2*phase.real
            if not phase:
                continue
            key="".join(label)
            value=phase*x*y
            out.setdefault(key,[]).append(complex(_real(value.real),_real(value.imag)))
    out={label:_sum_complex(values) for label,values in out.items()}
    out={p:v for p,v in out.items() if v} or {"I"*n:0j}
    if len(out)>256:
        raise ResourceLimit("Pauli product exceeds 256 output terms")
    return dict(sorted(out.items()))


def run(seed,reps):
    rng=random.Random(seed)
    rows=[]
    for n,axes in ((4,"IXYZ"),(6,"IZ"),(8,"IX")):
        labels=["".join(p) for p in itertools.product(axes,repeat=n)]
        size=min(64,len(labels))
        a=q.Observable({p:rng.uniform(-1,1) for p in rng.sample(labels,size)})
        b=q.Observable({p:rng.uniform(-1,1) for p in rng.sample(labels,size)})
        for mode in ("commutator","anticommutator","product"):
            expected=baseline(a,b,mode=mode)
            routes={"baseline":lambda:baseline(a,b,mode=mode),"candidate":lambda:_pauli_product(a,b,mode=mode)}
            timings={k:[] for k in routes}
            for _ in range(reps):
                for key in rng.sample(list(routes),len(routes)):
                    t=time.perf_counter_ns();actual=routes[key]();dt=(time.perf_counter_ns()-t)/1e6
                    assert actual==expected
                    timings[key].append(dt)
            rows.append(dict(n=n,axes=axes,seed=seed,mode=mode,pairs=size*size,output_terms=len(expected),
                             paths={k:stats(v) for k,v in timings.items()}))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=9);a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps({"scope":"matched internal algebra; exact coefficient dictionary equality","rows":[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]},indent=2,allow_nan=False))
