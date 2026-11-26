"""Measure direct row preparation against the earlier transpose/reparse path."""
import argparse,json,random,statistics,time
from pathlib import Path
import numpy as np
import ketary as q
from ketary._validation import _angle

def evaluate(n,count,seed=1101,reps=7):
    p=q.Circuit.parameter_vector("t",n)
    c=q.Circuit.symbolic(n).ry(p,range(n)).cx(pairs=q.chain(range(n)))
    rows=np.random.default_rng(seed).uniform(-1,1,(count,n)).tolist()
    def previous():
        parsed=tuple(tuple(_angle(x) for x in row) for row in rows)
        return c.sweep(**{x.name:tuple(row[i] for row in parsed) for i,x in enumerate(c.parameters)})
    def direct():return c.sweep_rows(rows)
    builders={"previous_transpose":previous,"direct_rows":direct}
    a,b=previous(),direct()
    assert a.bindings==b.bindings
    for x,y in zip(a.run(),b.run(),strict=True):
        np.testing.assert_allclose(x.math.statevector(),y.math.statevector(),rtol=0,atol=1e-9)
    samples={k:[] for k in builders};rng=random.Random(seed)
    for _ in range(reps):
        order=list(builders);rng.shuffle(order)
        for k in order:
            t=time.perf_counter_ns();builders[k]();samples[k].append((time.perf_counter_ns()-t)/1e6)
    return dict(n=n,count=count,seed=seed,variants={k:dict(raw_ms=v,p50_ms=statistics.median(v),p95_ms=float(np.quantile(v,.95))) for k,v in samples.items()})
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);p.add_argument("--reps",type=int,default=7);a=p.parse_args()
    if not 3<=a.reps<=30:p.error("3..30 repetitions")
    rows=[]
    for n in (2,4,6):
        for count in (1,8,32):
            row=evaluate(n,count,a.seed,a.reps);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps(dict(scope="shared CI preparation diagnostic; previous path emulates prior row validation/transpose, not exact old installed wheel",rows=rows),indent=2))
if __name__=="__main__":main()
