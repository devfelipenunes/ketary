"""Issue #306: cancellation audit and isolated dense/streamed RSS.

Independent analytic identity-shift oracle; no change to runtime or tolerances.
"""
import argparse,json,math,random,statistics,subprocess,sys,time
from pathlib import Path
import numpy as np
import ketary as q
from research.chunked_pauli import previous
from research.performance_memory_closure import own_memory

def analytic_case(n,shift,theta):
    # Product of a one-qubit rotation and zeros. H = shift I + Z0.
    v=np.zeros(1<<n,complex);v[:2]=[math.cos(theta/2),math.sin(theta/2)]
    r=q.Result(v);label="I"*(n-1)+"Z"
    h=q.Observable({"I"*n:shift,label:1.})
    centered=q.Observable({label:1.})
    return r,h,centered,math.sin(theta)**2

def cancellation(n,shift,theta):
    r,h,centered,want=analytic_case(n,shift,theta)
    before=r.math.statevector()
    routes={"streamed":r.math.observable_variance_streamed,
            "fallback":lambda op:r.math.observable_variance_streamed(op,max_bytes=64*(1<<n))}
    if n<=8:routes["dense"]=r.math.observable_variance
    values={}
    for key,fn in routes.items():
        actual=fn(h);stable=fn(centered)
        # The centered oracle is a separate diagnostic, not a new runtime
        # implementation; never hide deviations of the actual public call.
        assert abs(stable-want)<=1e-9
        values[key]=dict(value=actual,error=abs(actual-want),within_1e9=abs(actual-want)<=1e-9,
                         centered=stable,centered_error=abs(stable-want))
    np.testing.assert_array_equal(r.math.statevector(),before)
    return dict(n=n,shift=shift,theta=theta,expected=want,variants=values)

def fixture(n,count):
    rng=np.random.default_rng(306+n)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    terms={}
    while len(terms)<count:
        terms["".join(rng.choice(list("IXYZ"),n))]=float(rng.uniform(-.5,.5))
    r=q.Result(v);h=q.Observable(terms)
    return r,h

def worker(n,count,variant,reps):
    if n not in (4,8,12,16) or count not in (4,16) or not 3<=reps<=30:raise ValueError("bounded diagnostic")
    r,h=fixture(n,count)
    fn={"dense":lambda:r.math.observable_variance(h),
        "streamed":lambda:r.math.observable_variance_streamed(h),
        "legacy":lambda:previous(r,h)}[variant]
    if variant=="dense" and n>8:raise ValueError("dense cap")
    before=own_memory();samples=[]
    for _ in range(reps):
        t=time.perf_counter_ns();actual=fn();samples.append((time.perf_counter_ns()-t)/1e6)
    after=own_memory()
    # Oracle runs after memory measurement so dense/reference work does not
    # contaminate the measured route's HWM.
    expected=previous(r,h)
    if n<=8:
        from qiskit.quantum_info import SparsePauliOp
        v=r.math.statevector();v/=np.linalg.norm(v)
        matrix=SparsePauliOp.from_list(list(h.to_dict(n).items())).to_matrix()
        hv=matrix@v;delta=hv-np.vdot(v,hv)*v
        independent=float(np.vdot(delta,delta).real)
        assert abs(expected-independent)<=1e-9
    assert abs(actual-expected)<=1e-9
    return dict(n=n,count=count,variant=variant,value=actual,error=abs(actual-expected),
                before=before,after=after,retained_snapshot_bytes=16*(1<<n),
                raw_ms=samples,p50_ms=statistics.median(samples),p95_ms=float(np.quantile(samples,.95)))

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path)
    p.add_argument("--worker",action="store_true");p.add_argument("--n",type=int);p.add_argument("--count",type=int)
    p.add_argument("--variant",choices=("dense","streamed","legacy"));p.add_argument("--repetitions",type=int,default=7)
    a=p.parse_args()
    if a.worker:print(json.dumps(worker(a.n,a.count,a.variant,a.repetitions),allow_nan=False));return
    if not a.output:p.error("output required")
    cases=[cancellation(n,s,t) for n in (2,8,12) for s in (0.,2.**16,2.**30,2.**45) for t in (0.,1e-6,.37)]
    rows=[]
    for n in (4,8,12,16):
        for count in (4,16):
            variants=["streamed","legacy"]+(["dense"] if n<=8 else [])
            for rep in range(3):
                order=variants.copy();random.Random(n+count+rep).shuffle(order)
                for variant in order:
                    cmd=[sys.executable,"-m","research.variance_cancellation_rss","--worker","--n",str(n),"--count",str(count),"--variant",variant,"--repetitions",str(a.repetitions)]
                    row=dict(rep=rep,**json.loads(subprocess.check_output(cmd,text=True,timeout=90)))
                    rows.append(row);print(json.dumps(row,allow_nan=False),flush=True)
    for row in cases:print(json.dumps(dict(kind="cancellation",**row),allow_nan=False),flush=True)
    a.output.write_text(json.dumps(dict(scope="isolated Linux HWM; preparation included in baseline; cancellation deviations recorded, not accepted as PASS",cancellation=cases,rss=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
