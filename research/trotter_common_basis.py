"""Bounded phase-strict Trotter cost/accuracy qualification (#287)."""
import argparse,itertools,json,random,statistics,time
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from qiskit import transpile
from qiskit.quantum_info import Operator,Statevector
import ketary as q

PAULI={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),
       "Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}

def matrix(label):
    out=np.ones((1,1),complex)
    for x in label:out=np.kron(out,PAULI[x])
    return out

def bound(mats,t,steps,order):
    total=0.
    for i,a in enumerate(mats):
        b=sum(mats[i+1:],np.zeros_like(a));ab=a@b-b@a
        if order==1:total+=np.linalg.norm(ab,2)/2
        else:total+=np.linalg.norm(a@ab-ab@a,2)/24+np.linalg.norm(b@ab-ab@b,2)/12
    return min(2.,float(total)*abs(t)**(order+1)/steps**order)

def evaluate(seed,t,steps,order,reps):
    if seed not in (1101,2202,3303) or t not in (-.7,.3,1.1) or steps not in (1,4,16) or order not in (1,2) or not 3<=reps<=30:
        raise ValueError("bounded diagnostic")
    n=2+seed%2;rng=np.random.default_rng(seed)
    labels=["".join(x) for x in itertools.product("IXYZ",repeat=n) if any(c!="I" for c in x)]
    terms=dict(sorted([(str(k),float(v)) for k,v in zip(rng.choice(labels,3,replace=False),rng.uniform(-1,1,3))]+[("I"*n,.37)]))
    mats=[v*matrix(k) for k,v in terms.items()]
    exact=expm(-1j*t*sum(mats))
    seq=mats if order==1 else mats+mats[::-1]
    step=np.eye(1<<n,dtype=complex)
    for a in seq:step=expm(-1j*t/(steps*order)*a)@step
    expected=np.linalg.matrix_power(step,steps)
    ceiling=bound(mats,t,steps,order)
    error=float(np.linalg.norm(expected-exact,2));assert error<=ceiling+2e-12
    h=q.Observable(terms)
    def build():return q.Circuit(n).evolve_product(h,time=t,steps=steps,order=order)
    native=build().to_qiskit()
    def lower():return transpile(native,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=seed)
    common=lower()
    for c in (native,common):
        np.testing.assert_allclose(Operator(c).data,expected,atol=1e-9,rtol=0)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    wanted=expected@v
    routes={"build":build,"common_lower":lower,"native_run":lambda:Statevector(v).evolve(native),
            "common_run":lambda:Statevector(v).evolve(common)}
    raw={k:[] for k in routes};orders=[];rnd=random.Random(seed+steps+order)
    for _ in range(reps):
        names=list(routes);rnd.shuffle(names);orders.append(names)
        for name in names:
            start=time.perf_counter_ns();out=routes[name]();raw[name].append((time.perf_counter_ns()-start)/1e6)
            if name.endswith("_run"):np.testing.assert_allclose(out.data,wanted,atol=1e-9,rtol=0)
    return dict(seed=seed,n=n,t=t,steps=steps,order=order,approximation_error=error,analytical_bound=ceiling,
        native_residual=float(np.max(np.abs(Operator(native).data-expected))),
        common_residual=float(np.max(np.abs(Operator(common).data-expected))),
        gates=len(native.data),depth=native.depth(),common_gates=len(common.data),common_depth=common.depth(),
        common_cx=int(common.count_ops().get("cx",0)),state_payload_bytes=v.nbytes,trial_order=orders,
        variants={k:dict(raw_ms=s,p50_ms=statistics.median(s),p95_ms=float(np.quantile(s,.95))) for k,s in raw.items()})

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--repetitions",type=int,default=7)
    a=p.parse_args();rows=[]
    for seed in (1101,2202,3303):
        for t in (-.7,.3,1.1):
            for steps in (1,4,16):
                for order in (1,2):
                    row=evaluate(seed,t,steps,order,a.repetitions);rows.append(row);print(json.dumps(row,allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(scope="ideal ordered time-independent formulas; shared CI; common u/cx at level 0; not RSS or universal convergence",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
