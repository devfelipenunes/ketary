"""Research-only suffix transaction for compute/action/uncompute.

No runtime dispatch. Exact built-in Circuit, trusted nonconcurrent callers.
"""
import argparse,json,random,statistics,time
from pathlib import Path
import numpy as np
import ketary as q
from ketary._ergonomics import _selection
from qiskit.quantum_info import Operator
from research.expressive_composition_cost import workload,_one_staged_copy

def suffix_transaction(c,u,v,cw,aw):
    if any(type(x) is not q.Circuit for x in (c,u,v)):
        raise TypeError("research route requires exact Circuit")
    cw=_selection(c,cw);aw=_selection(c,aw)
    ci=c._composition_wires(u,cw)
    ai=c._composition_wires(v,aw)
    inv=u.inverse()
    raw=c._qc
    # Freeze aliased sources before the first append.
    source=raw.copy() if u is c or v is c else None
    uraw=source if u is c else u._qc
    vraw=source if v is c else v._qc
    start=len(raw.data);phase=raw.global_phase
    try:
        for block,wires in ((uraw,ci),(vraw,ai),(inv._qc,ci)):
            raw.compose(block,qubits=wires,inplace=True)
    except Exception:
        del raw.data[start:]
        raw.global_phase=phase
        raise
    if raw.global_phase!=phase:
        c._named_checkpoints={}
    return c

def evaluate(prefix,reps):
    if prefix not in (32,1000,10000) or not 3<=reps<=100:
        raise ValueError("unsupported workload")
    c,u,v,cw,aw=workload(prefix)
    before=c.to_qiskit();un=u.to_qiskit();vn=v.to_qiskit()
    def current():return c.copy().compute_action_uncompute(u,v,compute_wires=cw,action_wires=aw)
    def staged():return _one_staged_copy(c.copy(),u,v,cw,aw)
    def suffix():return suffix_transaction(c.copy(),u,v,cw,aw)
    expected=before.copy()
    for block,wires in ((un,cw),(vn,aw),(un.inverse(),cw)):
        expected.compose(block,qubits=list(wires),inplace=True)
    matrix=Operator(expected).data
    routes={"current":current,"staged":staged,"suffix":suffix}
    errors={}
    for name,fn in routes.items():
        out=fn()
        assert out.to_qiskit()==expected and out.checkpoints=={}
        err=float(np.max(np.abs(Operator(out.to_qiskit()).data-matrix)))
        assert err<=1e-9
        errors[name]=err
    samples={k:[] for k in routes};orders=[];rng=random.Random(412+prefix)
    for i in range(reps+3):
        order=list(routes);rng.shuffle(order)
        if i>=3:orders.append(order)
        for name in order:
            start=time.perf_counter_ns();out=routes[name]();dt=(time.perf_counter_ns()-start)/1e6
            if i>=3:samples[name].append(dt)
            del out
    assert c.to_qiskit()==before and u.to_qiskit()==un and v.to_qiskit()==vn
    return dict(prefix=prefix,errors=errors,orders=orders,
                variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=30)
    a=p.parse_args()
    rows=[]
    for rep in range(3):
        for prefix in (32,1000,10000):
            row=dict(rep=rep,**evaluate(prefix,a.repetitions));rows.append(row);print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(scope="shared runner; includes identical caller copy; trusted exact Circuit research only",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
