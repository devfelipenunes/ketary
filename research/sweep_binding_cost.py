"""Paired public sweep binding study, including previous row dispatch."""
import argparse,json,random,time
from pathlib import Path
from unittest.mock import patch
import numpy as np
import ketary as q
from qiskit.quantum_info import Operator
from ketary._ergonomics import SweepPlan
from research.native_stage_profile import stats

def previous(self,circuit,rows,params):
    self._payloads=tuple(circuit.bind({params[name]:v for name,v in row}) for row in rows)
    self._rows=rows
    self._width=circuit.num_qubits

def evaluate(n,layers,count,seed=1101,reps=7):
    rng=np.random.default_rng(seed);p=q.Circuit.parameter_vector("p",n)
    c=q.Circuit.symbolic(n)
    for k in range(layers):
        c.ry([v*(k+1)/layers for v in p],range(n)).cx(pairs=q.chain(range(n)))
    c.evolve(q.I(),time=p[0])
    raw=c.to_qiskit();params=c.parameters
    rows=tuple(tuple(float(v) for v in row) for row in rng.uniform(-.8,.8,(count,n)))
    named={key.name:tuple(row[i] for row in rows) for i,key in enumerate(params)}
    expected=tuple(raw.assign_parameters(dict(zip(params,row,strict=True)),inplace=False,flat_input=True) for row in rows)
    def verify(plan):
        assert len(plan._payloads)==count
        for payload,native in zip(plan._payloads,expected,strict=True):
            assert payload.to_qiskit()==native
        if n<=4:
            np.testing.assert_allclose(Operator(plan._payloads[-1].to_qiskit()).data,Operator(expected[-1]).data,rtol=0,atol=1e-9)
    routes={"named":lambda:c.sweep(**named),"ordered":lambda:c.sweep_rows(rows)}
    for fn in routes.values():verify(fn())
    with patch.object(SweepPlan,"_initialize_rows",previous):
        for fn in routes.values():verify(fn())
    samples={k+"_"+mode:[] for k in routes for mode in ("old","new")}
    samples.update({k:[] for k in ("public_identity","public_name","public_order","native_assignment")})
    row=rows[0];mapping=dict(zip(params,row,strict=True))
    others={"public_identity":lambda:c.bind(mapping),"public_name":lambda:c.bind(**{k.name:v for k,v in mapping.items()}),"public_order":lambda:c.bind(row),"native_assignment":lambda:raw.assign_parameters(mapping,inplace=False,flat_input=True)}
    rnd=random.Random(seed)
    for _ in range(reps):
        for k in rnd.sample(list(samples),len(samples)):
            if k in others:
                t=time.perf_counter_ns();out=others[k]();samples[k].append((time.perf_counter_ns()-t)/1e6)
                assert (out if k=="native_assignment" else out.to_qiskit())==expected[0]
            else:
                route,mode=k.split("_")
                if mode=="old":
                    with patch.object(SweepPlan,"_initialize_rows",previous):
                        t=time.perf_counter_ns();out=routes[route]();samples[k].append((time.perf_counter_ns()-t)/1e6)
                else:
                    t=time.perf_counter_ns();out=routes[route]();samples[k].append((time.perf_counter_ns()-t)/1e6)
                assert all(p.to_qiskit()==v for p,v in zip(out._payloads,expected,strict=True))
    assert c.to_qiskit()==raw
    return dict(n=n,layers=layers,gates=len(raw.data),rows=count,seed=seed,stages={k:stats(v) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for n in (2,4,8):
        for layers in (1,4,8):
            for count in (1,8,32):
                row=evaluate(n,layers,count,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="paired public sweep plan construction; previous row dispatch emulated; no execution timing; shared CI",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
