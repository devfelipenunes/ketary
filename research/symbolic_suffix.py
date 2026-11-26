"""Research-only symbolic append transaction using public native data deletion.

No runtime patch. Tests exercise parameter-table recovery after partial
native append and same-name/different-identity collision.
"""
import argparse,json,random,time
from pathlib import Path
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from research.native_stage_profile import stats

def suffix(raw,append):
    start=len(raw.data);phase=raw.global_phase
    try:append(raw)
    except Exception:
        del raw.data[start:]
        raw.global_phase=phase
        raise
    return raw

def staged(raw,append):
    candidate=raw.copy();append(candidate);return candidate

def evaluate(n,layers,seed=1101,reps=7):
    rng=np.random.default_rng(seed);p=q.Circuit.parameter_vector("p",n)
    values=rng.uniform(-.7,.7,n).tolist()
    def build(route):
        raw=QuantumCircuit(n)
        for k in range(layers):
            def add(c):
                for i in range(n):c.ry(p[i]*(k+1)/layers,i)
            raw=route(raw,add)
            raw=route(raw,lambda c:c.cx(list(range(n-1)),list(range(1,n))))
        return raw
    reference=build(staged);candidate=build(suffix)
    assert reference==candidate and tuple(reference.parameters)==tuple(candidate.parameters)
    expected=reference.assign_parameters(values)
    assert candidate.assign_parameters(values)==expected
    if n<=4:
        np.testing.assert_allclose(Operator(candidate.assign_parameters(values)).data,Operator(expected).data,rtol=0,atol=1e-9)
    routes={"staged":staged,"suffix":suffix}
    samples={k:[] for k in routes};rnd=random.Random(seed)
    for _ in range(reps):
        for k in rnd.sample(list(routes),2):
            t=time.perf_counter_ns();actual=build(routes[k]);samples[k].append((time.perf_counter_ns()-t)/1e6)
            assert actual==reference
    return dict(n=n,layers=layers,gates=len(reference.data),seed=seed,variants={k:stats(v) for k,v in samples.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for n in (4,8,12):
        for layers in (4,16,64):
            row=evaluate(n,layers,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="native symbolic suffix research only; no SDK promotion or concurrency claim",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
