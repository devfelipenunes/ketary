"""Paired public angle/binding cost with exact previous numeric validator."""
import argparse,json,math,random,time
from numbers import Real
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import numpy as np
import ketary as q
from ketary import _validation,_adapter,_circuit
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from research.native_stage_profile import stats

def previous_angle(value):
    if isinstance(value,(bool,np.bool_)) or not isinstance(value,Real):
        raise ValueError("rotation angle must be a finite real number in radians")
    try:
        angle=float(value)
    except (ValueError,OverflowError,TypeError) as exc:
        raise ValueError("invalid rotation angle") from exc
    if not math.isfinite(angle):
        raise ValueError("rotation angle must be finite")
    return angle

def evaluate(n,count,seed=1101,reps=7):
    rng=np.random.default_rng(seed)
    p=q.Circuit.parameter_vector("p",count)
    values=tuple(float(x) for x in rng.uniform(-.8,.8,count))
    c=q.Circuit.symbolic(n);native=QuantumCircuit(n)
    for i in range(count):
        c.ry(p[i],i%n);native.ry(p[i],i%n)
    bindings=dict(zip(p,values,strict=True))
    expected=native.assign_parameters(bindings,inplace=False,flat_input=True)
    assert c.to_qiskit()==native
    def build():
        out=q.Circuit(n)
        for i,value in enumerate(values):out.ry(value,i%n)
        return out
    routes={"validate":lambda:tuple(_validation._angle(x) for x in values),
            "bind":lambda:c.bind(bindings),"build":build}
    samples={k+"_"+mode:[] for k in routes for mode in ("old","new")}
    rnd=random.Random(seed)
    for _ in range(reps):
        for k in rnd.sample(list(samples),len(samples)):
            route,mode=k.split("_")
            with ExitStack() as stack:
                if mode=="old":
                    for module in (_validation,_adapter,_circuit):
                        stack.enter_context(patch.object(module,"_angle",previous_angle))
                t=time.perf_counter_ns();out=routes[route]();samples[k].append((time.perf_counter_ns()-t)/1e6)
            if route=="validate":assert out==values
            else:
                raw=out.to_qiskit();assert raw==expected
                if n<=4:np.testing.assert_allclose(Operator(raw).data,Operator(expected).data,rtol=0,atol=1e-9)
    assert c.to_qiskit()==native
    return dict(n=n,parameters=count,seed=seed,stages={k:stats(v) for k,v in samples.items()})
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for n in (2,4,8):
        for count in (16,128,512):
            row=evaluate(n,count,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="exact Python float validator; old validator reproduced; public binding/build and validation; shared CI",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
