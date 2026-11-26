"""Paired same-public-path batch preflight attribution."""
import argparse,json,random,statistics,time
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
from collections.abc import Mapping
from itertools import islice
import numpy as np
import ketary as q
from ketary import _ergonomics
from ketary._validation import ResourceLimit
from ketary._ergonomics import _native_batch

def previous_selection(c,wires):
    if isinstance(wires,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected an ordered iterable of wires")
    try:
        selected=tuple(c.gates._wire(w) for w in islice(iter(wires),min(c.num_qubits,4096)+1))
    except TypeError as exc:
        raise ValueError("expected an ordered iterable of wires") from exc
    if not selected or len(selected)>min(c.num_qubits,4096) or len(set(selected))!=len(selected):
        raise ValueError("expected nonempty distinct wires, at most 4096")
    return selected

def previous_pairs(c,name,a,b,pairs,*params):
    """Explicit ordered pair placement; no implicit zip or Cartesian mode."""
    if pairs is None:
        return getattr(c.gates,name)(*params,a,b)
    if a is not None or b is not None:
        raise ValueError("choose scalar wires or pairs, not both")
    if isinstance(pairs,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected ordered wire pairs")
    gate=c.gates
    selected=[]
    try:
        for row in islice(iter(pairs),10001):
            if isinstance(row,(str,bytes,Mapping,set,frozenset)):
                raise ValueError("expected ordered wire pair")
            pair=tuple(islice(iter(row),3))
            if len(pair)!=2:
                raise ValueError("each pair must contain two distinct wires")
            selected.append(gate._pair(*pair))
    except TypeError as exc:
        raise ValueError("expected ordered wire pairs") from exc
    if not selected:
        raise ValueError("expected at least one wire pair")
    if len(selected)>10000:
        raise ResourceLimit("pair batch supports at most 10000 pairs")
    # Only single-angle gates support aligned rows. Keep the established
    # native scalar broadcast unchanged, including symbolic parameters.
    if len(params)==1:
        theta=params[0]
        if isinstance(theta,(str,bytes,Mapping,set,frozenset)):
            raise ValueError("expected scalar angle or ordered angle sequence")
        try:
            angles=iter(theta)
        except TypeError:
            pass
        else:
            values=tuple(islice(angles,len(selected)+1))
            if len(values)!=len(selected):
                raise ValueError("angle and pair sequences must have equal length")
            values=tuple(c._gate_angle(v) for v in values)
            def append(native):
                method=getattr(native,name)
                for (first,second),angle in zip(selected,values,strict=True):
                    method(angle,first,second)
            return _native_batch(c,append)
    values=tuple(c._gate_angle(p) for p in params)
    first,second=zip(*selected,strict=True)
    return _native_batch(c,lambda native:getattr(native,name)(*values,list(first),list(second)))



def evaluate(kind,layers,reps):
    if kind not in ("single","pairs") or layers not in (100,1000) or not 3<=reps<=100:
        raise ValueError("unsupported diagnostic case")
    n=8;rows=tuple((i,(i+1)%n) for i in range(n))
    def build():
        c=q.Circuit(n)
        for _ in range(layers):
            if kind=="single":c.h(range(n))
            else:c.cz(pairs=rows)
        return c
    functions={"previous":(previous_selection,previous_pairs),
               "candidate":(_ergonomics._selection,_ergonomics._pairs)}
    def route(name):
        stack=ExitStack()
        for attr,fn in zip(("_selection","_pairs"),functions[name],strict=True):
            stack.enter_context(patch.object(_ergonomics,attr,fn))
        return stack
    with route("previous"):expected=build().to_qiskit()
    with route("candidate"):assert build().to_qiskit()==expected
    samples={k:[] for k in functions};orders=[];rng=random.Random(layers)
    for i in range(reps+3):
        order=list(functions);rng.shuffle(order)
        if i>=3:orders.append(order)
        for name in order:
            with route(name):
                start=time.perf_counter_ns();out=build();elapsed=(time.perf_counter_ns()-start)/1e6
            if i>=3:samples[name].append(elapsed)
            del out
    return dict(kind=kind,layers=layers,gates=n*layers,orders=orders,
                variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=20)
    a=p.parse_args();rows=[evaluate(k,n,a.repetitions) for k in ("single","pairs") for n in (100,1000)]
    for row in rows:print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(rows,indent=2,allow_nan=False))
if __name__=="__main__":main()
