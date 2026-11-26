"""Matched scalar fluent dispatch diagnostic; shared CI, not release evidence."""
import argparse,json,random,statistics,time
from pathlib import Path
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from benchmark import mixed_workload

class Previous(q.Circuit):
    """Previous fluent method bodies; inherits unchanged validators."""
    def h(self,q):
        from ketary._ergonomics import _single
        return _single(self,"h",q)

    def x(self,q):
        from ketary._ergonomics import _single
        return _single(self,"x",q)

    def y(self,q):
        from ketary._ergonomics import _single
        return _single(self,"y",q)

    def z(self,q):
        from ketary._ergonomics import _single
        return _single(self,"z",q)

    def s(self,q):
        from ketary._ergonomics import _single
        return _single(self,"s",q)

    def sdg(self,q):
        from ketary._ergonomics import _single
        return _single(self,"sdg",q)

    def t(self,q):
        from ketary._ergonomics import _single
        return _single(self,"t",q)

    def tdg(self,q):
        from ketary._ergonomics import _single
        return _single(self,"tdg",q)

    def sx(self,q):
        from ketary._ergonomics import _single
        return _single(self,"sx",q)

    def sxdg(self,q):
        from ketary._ergonomics import _single
        return _single(self,"sxdg",q)

    def rx(self,theta,q):
        from ketary._ergonomics import _rotation
        return _rotation(self,"rx",theta,q)

    def ry(self,theta,q):
        from ketary._ergonomics import _rotation
        return _rotation(self,"ry",theta,q)

    def rz(self,theta,q):
        from ketary._ergonomics import _rotation
        return _rotation(self,"rz",theta,q)

    def p(self,theta,q):
        from ketary._ergonomics import _rotation
        return _rotation(self,"p",theta,q)

    def u(self,theta,phi,lam,q):
        from ketary._ergonomics import _single
        return _single(self,"u",q,theta,phi,lam)

def evaluate(count,reps):
    if count not in (1000,10000) or not 3<=reps<=100:
        raise ValueError("unsupported workload")
    ops=mixed_workload(8,count)
    def build(cls):
        c=cls(8)
        for name,args in ops:getattr(c,name)(*args)
        return c
    variants={"previous":lambda:build(Previous),"candidate":lambda:build(q.Circuit),"native":lambda:build(QuantumCircuit)}
    expected=variants["native"]()
    for key in ("previous","candidate"):
        assert variants[key]().to_qiskit()==expected
    samples={k:[] for k in variants}
    rng=random.Random(911+count);orders=[]
    for i in range(reps+3):
        order=list(variants);rng.shuffle(order)
        if i>=3:orders.append(order)
        for key in order:
            t=time.perf_counter_ns();result=variants[key]();elapsed=(time.perf_counter_ns()-t)/1e6
            if i>=3:samples[key].append(elapsed)
            del result
    return dict(gates=count,orders=orders,scope="previous method bodies in a subclass, identical validators; exact ordered circuit equality",
                variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=20)
    a=p.parse_args();rows=[evaluate(n,a.repetitions) for n in (1000,10000)]
    for row in rows:print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(rows,indent=2,allow_nan=False))
if __name__=="__main__":main()
