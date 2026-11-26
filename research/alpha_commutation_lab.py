"""Independent mathematical experiment: symplectic commutation grouping.

Research only; group membership does not imply simultaneous measurement
without basis synthesis. General commuting and qubit-wise commuting differ.
"""
import argparse
import itertools
import json
import random
import time
from research.circuit_rewrite_ladder import stats

def masks(label):
    x=z=0
    for p in label:
        x=(x<<1)|int(p in "XY")
        z=(z<<1)|int(p in "YZ")
    return x,z

def direct(a,b,qwc):
    conflicts=sum(x!="I" and y!="I" and x!=y for x,y in zip(a,b,strict=True))
    return conflicts==0 if qwc else conflicts%2==0

def packed(a,b,qwc):
    x,z=a;u,v=b
    conflict=(x&v)^(z&u)
    return conflict==0 if qwc else conflict.bit_count()%2==0

def partition(labels,qwc,use_masks):
    keys={p:masks(p) for p in labels} if use_masks else None
    groups=[]
    for p in labels:
        for group in groups:
            if all(packed(keys[p],keys[q],qwc) if use_masks else direct(p,q,qwc) for q in group):
                group.append(p);break
        else:groups.append([p])
    return groups

def run(seed,reps,quick=False):
    rng=random.Random(seed);rows=[]
    for n,count in (((3,32),) if quick else ((4,64),(8,128),(12,256),(20,256))):
        labels=set()
        while len(labels)<count:labels.add("".join(rng.choice("IXYZ") for _ in range(n)))
        labels=sorted(labels)
        for qwc in (False,True):
            ref=partition(labels,qwc,False)
            for group in ref:
                assert all(direct(p,q,qwc) for p,q in itertools.combinations(group,2))
            paths={"direct":lambda:partition(labels,qwc,False),"packed":lambda:partition(labels,qwc,True)}
            timing={k:[] for k in paths}
            for _ in range(reps):
                for k in rng.sample(list(paths),len(paths)):
                    t=time.perf_counter_ns();actual=paths[k]();dt=(time.perf_counter_ns()-t)/1e6
                    assert actual==ref
                    timing[k].append(dt)
            rows.append(dict(n=n,terms=count,qwc=qwc,seed=seed,groups=len(ref),paths={k:stats(v) for k,v in timing.items()}))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=9);p.add_argument("--quick",action="store_true");a=p.parse_args()
    if a.reps<1:p.error("positive reps required")
    print(json.dumps(dict(scope="identical deterministic first-fit grouping; no minimal coloring or measurement claim",
        rows=[r for seed in (1101,2202,3303) for r in run(seed,a.reps,a.quick)]),indent=2,allow_nan=False))
