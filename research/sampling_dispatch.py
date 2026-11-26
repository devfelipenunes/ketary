"""Compare exact seeded multinomial dispatch, not a changed sampling law."""
import argparse,json,random,time,resource,subprocess,sys
from pathlib import Path
import numpy as np
import ketary as q
from research.query_plan_cost import stats

def previous(r,shots,seed):
    p=np.abs(r._data)**2;p/=p.sum()
    counts=np.random.default_rng(seed).multinomial(shots,p)
    return {format(i,f"0{r.num_qubits}b"):int(v) for i,v in enumerate(counts) if v}

def fixture(n,seed):
    # Deterministic complex snapshot; construction excluded from timing.
    rng=np.random.default_rng(seed)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    return q.Result(v)

def evaluate(n,shots,seed=1101,reps=5):
    r=fixture(n,seed)
    routes={"previous":lambda:previous(r,shots,seed),
            "current":lambda:r.sample(shots=shots,seed=seed)}
    expected=routes["previous"]();assert routes["current"]()==expected
    samples={k:[] for k in routes};rnd=random.Random(seed)
    for _ in range(reps):
        for k in rnd.sample(list(routes),2):
            t=time.perf_counter_ns();out=routes[k]();samples[k].append((time.perf_counter_ns()-t)/1e6)
            assert out==expected and list(out)==list(expected)
    return dict(n=n,shots=shots,seed=seed,identical=True,outcomes=len(expected),variants={k:stats(v) for k,v in samples.items()})

def rss_worker(n,shots,seed,route):
    r=fixture(n,seed)
    before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out=previous(r,shots,seed) if route=="previous" else r.sample(shots=shots,seed=seed)
    after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux reports KiB. This is whole-process high-water, not isolated scratch.
    return dict(route=route,n=n,shots=shots,seed=seed,before_peak_kib=before,after_peak_kib=after,total=sum(out.values()))

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path);p.add_argument("--seed",type=int,default=1101)
    p.add_argument("--worker",choices=["previous","current"]);p.add_argument("--n",type=int);p.add_argument("--shots",type=int)
    a=p.parse_args()
    if a.worker:
        print(json.dumps(rss_worker(a.n,a.shots,a.seed,a.worker)));return
    if not a.output:p.error("--output required")
    rows=[]
    for n in (4,12,16,20):
        for shots in (1,32,1024):
            row=evaluate(n,shots,a.seed);rows.append(row);print(json.dumps(row),flush=True)
    rss=[]
    if sys.platform.startswith("linux"):
        for route in ("previous","current"):
            for n in (16,20):
                out=subprocess.check_output([sys.executable,"-m","research.sampling_dispatch","--worker",route,"--n",str(n),"--shots","32","--seed",str(a.seed)],text=True)
                row=json.loads(out);rss.append(row);print(json.dumps({"rss":row}),flush=True)
    a.output.write_text(json.dumps(dict(scope="shared CI exact seeded multinomial; child process Linux peak RSS includes fixture/imports",rows=rows,rss=rss),indent=2,allow_nan=False))
if __name__=="__main__":main()
