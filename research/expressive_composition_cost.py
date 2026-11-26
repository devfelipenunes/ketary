"""Stage attribution for idiomatic compute/action/uncompute workflows.

Research alternative uses an independent staging copy; no SDK change.
"""
import argparse
import json
import random
import statistics
import time
from pathlib import Path

import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

def _one_staged_copy(c,u,v,cw,aw):
    """Narrow bound research route, not a public replacement."""
    ci=c._composition_wires(u,cw)
    ai=c._composition_wires(v,aw)
    inverse=u.inverse()
    candidate=c._qc.copy()
    for block,wires in ((u,ci),(v,ai),(inverse,ci)):
        candidate.compose(block._qc,qubits=wires,inplace=True)
    if candidate.global_phase!=c._qc.global_phase:
        c._named_checkpoints={}
    c._qc=candidate
    return c

def workload(prefix,alias=False):
    native=QuantumCircuit(4)
    for i in range(prefix):
        native.ry(.013*(i%13),i%4)
    c=q.from_qiskit(native).checkpoint("prefix")
    u=q.Circuit(2).h(0).cx(0,1).evolve(q.I(1),time=.13)
    v=q.Circuit(1).rz(.37,0).evolve(q.I(),time=.23)
    if alias:
        u=c
        cw=(3,1,0,2)
    else:
        cw=(3,0)
    return c,u,v,cw,(0,)

def evaluate(prefix,reps):
    if prefix not in (32,1000,10000) or not 3<=reps<=100:
        raise ValueError("unsupported diagnostic workload")
    c,u,v,cw,aw=workload(prefix)
    before=c.to_qiskit();un=u.to_qiskit();vn=v.to_qiskit()
    def old():
        return c.copy().compute_action_uncompute(u,v,compute_wires=cw,action_wires=aw)
    def candidate():
        return _one_staged_copy(c.copy(),u,v,cw,aw)
    ref=before.copy()
    ref.compose(un,qubits=list(cw),inplace=True)
    ref.compose(vn,qubits=list(aw),inplace=True)
    ref.compose(un.inverse(),qubits=list(cw),inplace=True)
    expected=Operator(ref).data
    residual={}
    for name,fn in (("current",old),("one_staged_copy",candidate)):
        result=fn()
        np.testing.assert_allclose(Operator(result.to_qiskit()).data,expected,atol=1e-9,rtol=0)
        assert result.checkpoints=={}
        residual[name]=float(np.max(np.abs(Operator(result.to_qiskit()).data-expected)))
    variants={"current":old,"one_staged_copy":candidate}
    samples={k:[] for k in variants}
    rng=random.Random(700+prefix)
    orders=[]
    for i in range(reps+3):
        order=list(variants);rng.shuffle(order)
        if i>=3:orders.append(order)
        for key in order:
            start=time.perf_counter_ns();result=variants[key]();elapsed=(time.perf_counter_ns()-start)/1e6
            if i>=3:samples[key].append(elapsed)
            del result
    assert c.to_qiskit()==before and c.checkpoints=={"prefix":prefix}
    assert u.to_qiskit()==un and v.to_qiskit()==vn
    return dict(prefix=prefix,scope="shared runner; includes same caller-owned copy in both routes",
                residual=residual,orders=orders,
                variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--repetitions",type=int,default=20)
    args=parser.parse_args()
    rows=[evaluate(n,args.repetitions) for n in (32,1000,10000)]
    for row in rows:print(json.dumps(row,allow_nan=False),flush=True)
    args.output.write_text(json.dumps(rows,indent=2,allow_nan=False))
if __name__=="__main__":main()
