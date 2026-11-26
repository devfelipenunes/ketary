"""Attribute explicit QueryPlan costs; private snapshot comparator, not API."""
import argparse,json,random,statistics,time
from pathlib import Path
import numpy as np
import ketary as q

def timed(fn):
    t=time.perf_counter_ns();out=fn();return out,(time.perf_counter_ns()-t)/1e6
def stats(xs):return dict(raw_ms=xs,p50_ms=statistics.median(xs),p95_ms=float(np.quantile(xs,.95)))
def evidence(result,plan,budget,sizes=None):
    rows=[]
    for wires in plan.subsystems:
        m=result.math.density_matrix(wires,max_bytes=budget)
        rows.append(dict(wires=list(wires),real=m.real.tolist(),imag=m.imag.tolist()))
    return dict(schema_version=1,scope="one explicit ideal-state simulation",evidence=result.evidence(bits=plan.bits,paulis=plan.paulis),density_matrices=rows,estimate=plan.estimate() if sizes is None else sizes)
def compare_nested(a,b):
    if isinstance(a,dict):
        assert a.keys()==b.keys()
        return max((compare_nested(a[k],b[k]) for k in a),default=0.)
    if isinstance(a,list):
        assert len(a)==len(b)
        return max((compare_nested(x,y) for x,y in zip(a,b,strict=True)),default=0.)
    if isinstance(a,(int,float)):
        return abs(a-b)
    assert a==b
    return 0.
def evaluate(n,gates,seed=1101,reps=7):
    rng=np.random.default_rng(seed);c=q.Circuit(n)
    for i in range(gates):
        w=i%n
        if i%3==0:c.ry(float(rng.uniform(-1,1)),w)
        elif i%3==1:c.cx(w,(w+1)%n)
        else:c.rz(float(rng.uniform(-1,1)),w)
    bits=["0"*n,"1"*n];paulis=["Z"*n,"X"*n];subsystems=[(0,n-1)]
    plan,prepare_ms=timed(lambda:c.plan(bits=bits,paulis=paulis,subsystems=subsystems))
    snapshot,copy_ms=timed(c.copy)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    c.x(0) # prove source mutation does not change either private snapshot
    budget=64*1024**2
    want=plan.run(initial_state=v)
    samples={k:[] for k in ("estimate","decode","simulate","export","plan_total","private_snapshot_total")}
    rnd=random.Random(seed);residual=0.
    for _ in range(reps):
        for route in rnd.sample(["plan","snapshot"],2):
            if route=="plan":
                actual,ms=timed(lambda:plan.run(initial_state=v));samples["plan_total"].append(ms)
            else:
                def manual():return evidence(snapshot.run(initial_state=v),plan,budget)
                actual,ms=timed(manual);samples["private_snapshot_total"].append(ms)
            residual=max(residual,compare_nested(actual,want))
        sizes,ms=timed(plan.estimate);samples["estimate"].append(ms)
        decoded,ms=timed(lambda:q.Circuit.from_json(plan._circuit));samples["decode"].append(ms)
        result,ms=timed(lambda:decoded.run(initial_state=v));samples["simulate"].append(ms)
        # Use precomputed sizes: stage export excludes repeated estimate.
        def export():
            return evidence(result,plan,budget,sizes)
        actual,ms=timed(export);samples["export"].append(ms)
        residual=max(residual,compare_nested(actual,want))
    assert residual<1e-9
    return dict(n=n,gates=gates,seed=seed,prepare_ms=prepare_ms,copy_ms=copy_ms,max_error=residual,stages={k:stats(v) for k,v in samples.items()})
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);a=p.parse_args()
    rows=[]
    for n in (4,8,12):
        for gates in (32,256,1024):
            row=evaluate(n,gates,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="shared CI; private snapshot comparator retains JSON estimate; no public replacement or RSS claim",rows=rows),indent=2,allow_nan=False))
if __name__=="__main__":main()
