"""Pinned previous ordered product path vs current installed implementation."""
import argparse,json,random,time
import numpy as np
import ketary as q
from qiskit.quantum_info import Operator
from scipy.linalg import expm
from research.circuit_rewrite_ladder import stats

def previous(n,H,t,steps,order):
    c=q.Circuit(n);block=q.Circuit(n)
    terms=tuple((p,v) for p,v in H.to_dict(n).items() if v)
    seq=terms if order==1 else terms+terms[::-1]
    for p,v in seq:block.evolve(q.Observable({p:v}),time=t/(steps*order))
    return c.apply(block,times=steps)

def current(n,H,t,steps,order):
    return q.Circuit(n).evolve_product(H,time=t,steps=steps,order=order)

def run(seed,reps=9):
    rng=random.Random(seed)
    out=[]
    for n in (3,5,8):
        # Distinct X/Y/Z supports, mixed terms, identity and negative weights.
        labels=["I"*n]
        for i in range(n):
            for axis in "XYZ":
                p=list("I"*n);p[i]=axis;labels.append("".join(p))
            if i:
                p=list("I"*n);p[i-1]="Y";p[i]="Z";labels.append("".join(p))
        H=q.Observable({p:rng.uniform(-.8,.8) for p in labels})
        for order in (1,2):
            for steps in (1,8,16):
                args=(n,H,-.37,steps,order)
                expected=previous(*args).to_qiskit()
                actual=current(*args).to_qiskit()
                if n<=5:
                    ref=np.eye(1<<n,dtype=complex)
                    terms=list(H.to_dict(n).items())
                    seq=terms if order==1 else terms+terms[::-1]
                    step=np.eye(1<<n,dtype=complex)
                    for p,v in seq:step=expm(-1j*(-.37/(steps*order))*q.Observable({p:v}).to_qiskit().to_matrix())@step
                    ref=np.linalg.matrix_power(step,steps)
                    np.testing.assert_allclose(Operator(actual).data,ref,atol=1e-9,rtol=0)
                    np.testing.assert_allclose(Operator(expected).data,ref,atol=1e-9,rtol=0)
                assert actual.count_ops()==expected.count_ops()
                assert actual.data==expected.data
                assert abs(np.exp(1j*float(actual.global_phase))-np.exp(1j*float(expected.global_phase)))<1e-9
                samples={"previous":[],"current":[]}
                for _ in range(reps):
                    for route in rng.sample(list(samples),2):
                        start=time.perf_counter_ns()
                        c=(previous if route=="previous" else current)(*args)
                        samples[route].append((time.perf_counter_ns()-start)/1e6)
                        assert len(c.to_qiskit().data)==len(expected.data)
                out.append(dict(n=n,steps=steps,order=order,terms=len(labels),gates=len(expected.data),timing={k:stats(v) for k,v in samples.items()},ratio=float(np.median(samples["previous"])/np.median(samples["current"]))))
    return out
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    print(json.dumps(dict(seed=a.seed,baseline="4d6d7811",scope="previous installed per-term evolve path vs current, construction only; shared CI; old conservative caps retained",rows=run(a.seed)),indent=2,allow_nan=False))
