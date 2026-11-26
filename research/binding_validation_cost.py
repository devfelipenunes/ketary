"""Paired binding validation ablation; no skipped numeric or phase checks."""
import argparse,json,math,random,time
from pathlib import Path
import numpy as np
import ketary as q
from ketary._adapter import _validate_bound_values
from ketary._validation import _angle
from research.native_stage_profile import stats
from qiskit.quantum_info import Operator

def previous(qc):
    if qc.parameters:raise q.UnsupportedOperation("bind all symbolic parameters before this operation")
    for item in qc.data:
        for value in item.operation.params:_angle(value)
    if not math.isfinite(float(qc.global_phase)):raise ValueError("invalid global phase")

def evaluate(n,layers,seed=1101,reps=9):
    rng=np.random.default_rng(seed);p=q.Circuit.parameter_vector("p",n)
    c=q.Circuit.symbolic(n)
    for i in range(layers):
        c.ry([x*(i+1)/layers for x in p],range(n)).cx(pairs=q.chain(range(n)))
        c.rz(.21,range(n))
    row=dict(zip(p,rng.uniform(-.7,.7,n),strict=True))
    raw=c.to_qiskit();bound=raw.assign_parameters(row,inplace=False,flat_input=True)
    previous(bound);_validate_bound_values(bound)
    assert all(item.params==item.operation.params for item in bound.data)
    assert c.bind(row).to_qiskit()==bound
    if n<=4:np.testing.assert_allclose(Operator(c.bind(row).to_qiskit()).data,Operator(bound).data,rtol=0,atol=1e-9)
    def old_bind():
        result=raw.assign_parameters({k:_angle(v) for k,v in row.items()},inplace=False,flat_input=True);previous(result);return result
    routes={"old_validation":lambda:previous(bound),"new_validation":lambda:_validate_bound_values(bound),
            "old_assign_validate":old_bind,"new_assign_validate":lambda:c.bind(row)}
    samples={k:[] for k in routes};rnd=random.Random(seed)
    for _ in range(reps):
        for k in rnd.sample(list(routes),len(routes)):
            t=time.perf_counter_ns();out=routes[k]();samples[k].append((time.perf_counter_ns()-t)/1e6)
            if k=="old_assign_validate":assert out==bound
            if k=="new_assign_validate":assert out.to_qiskit()==bound
    return dict(n=n,layers=layers,gates=len(bound.data),seed=seed,stages={k:stats(v) for k,v in samples.items()})
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for n in (4,8,12):
        for layers in (4,16,64):
            row=evaluate(n,layers,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="previous validation emulation; shared CI; full numeric scan retained; old assign route excludes some public preflight",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
