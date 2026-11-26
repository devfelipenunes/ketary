"""Research candidates: depth-aware parity and two-CX XY synthesis.

Measure logical, common-basis, lowering and execution costs separately.
Not installed; do not replace a compact native simulator route automatically.
"""
import argparse
import json
import random
import time
import numpy as np
from scipy.linalg import expm
from qiskit import QuantumCircuit,transpile
from qiskit.quantum_info import Operator,Statevector
import ketary as q
from research.circuit_rewrite_ladder import stats

def xy_candidate(a,b):
    c=QuantumCircuit(2)
    c.rx(-np.pi/2,[0,1]);c.cx(0,1)
    c.rx(a,0);c.rz(b,1);c.cx(0,1)
    c.rx(np.pi/2,[0,1])
    return c

def xy_baseline(a,b):
    c=QuantumCircuit(2);c.rxx(a,0,1);c.ryy(b,0,1)
    return c

def parity_tree(active,root):
    # Preserve root as last element through pairwise reductions.
    live=[w for w in active if w!=root]+[root]
    edges=[]
    while len(live)>1:
        next_live=[]
        for i in range(0,len(live)-1,2):
            a,b=live[i:i+2];edges.append((a,b));next_live.append(b)
        if len(live)%2:next_live.append(live[-1])
        live=next_live
    assert live==[root]
    return edges

def depth_candidate(n,terms,t):
    c=QuantumCircuit(n);availability=[0]*n
    # Independent diagonal terms commute. Each candidate preserves exact
    # full parity, not just behavior on clean ancillas. Choose a root with
    # smallest predicted finish time; no mutable state shared across calls.
    pending=[]
    for label,w in sorted(terms.items()):
        active=tuple(i for i,a in enumerate(reversed(label)) if a=="Z")
        if not active:c.global_phase-=w*t
        else:pending.append((active,2*w*t))
    def schedule(edges,root):
        d=availability.copy()
        for a,b in edges:
            d[a]=d[b]=max(d[a],d[b])+1
        d[root]+=1
        for a,b in reversed(edges):
            d[a]=d[b]=max(d[a],d[b])+1
        return d
    while pending:
        choices=[]
        for i,(active,theta) in enumerate(pending):
            for root in active:
                edges=parity_tree(active,root)
                d=schedule(edges,root)
                choices.append((max(d),sum(d),i,root,edges,d))
        _,_,i,root,edges,availability=min(choices,key=lambda x:x[:4])
        _,theta=pending.pop(i)
        for a,b in edges:c.cx(a,b)
        c.rz(theta,root)
        for a,b in reversed(edges):c.cx(a,b)
    return c

def run(seed,reps):
    rng=random.Random(seed);nrng=np.random.default_rng(seed)
    fixtures=[]
    for a,b in ((.47,.47),(.31,-.56),(.0,.6)):
        X=np.array([[0,1],[1,0]]);Y=np.array([[0,-1j],[1j,0]])
        expected=expm(-.5j*(a*np.kron(X,X)+b*np.kron(Y,Y)))
        fixtures.append(("xy",2,{"baseline":lambda a=a,b=b:xy_baseline(a,b),
                                "candidate":lambda a=a,b=b:xy_candidate(a,b)},expected))
    for n in (4,5,6):
        terms={"I"*n:.17}
        for i in range(1,n-1):
            for j in range(i):
                label=["I"]*n
                for w in (i,j,n-1):label[n-1-w]="Z"
                terms["".join(label)]=rng.uniform(-1,1)
        terms["Z"*n]=.21
        t=.37
        diagonal=np.array([sum(w*(-1)**sum((k>>(n-1-i))&1 for i,a in enumerate(p) if a=="Z")
                               for p,w in terms.items()) for k in range(1<<n)])
        expected=np.diag(np.exp(-1j*t*diagonal))
        fixtures.append(("parity",n,{"baseline":lambda n=n,terms=terms:q.Circuit(n).evolve(q.Observable(terms),time=.37).to_qiskit(),
                                    "candidate":lambda n=n,terms=terms:depth_candidate(n,terms,.37)},expected))
    rows=[]
    for index,(kind,n,paths,expected) in enumerate(fixtures):
        v=nrng.normal(size=1<<n)+1j*nrng.normal(size=1<<n);v/=np.linalg.norm(v)
        metrics={}
        def lower(raw):
            return transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=seed,qubits_initially_zero=False)
        for name,fn in paths.items():
            raw=fn();common=lower(raw)
            for circuit in (raw,common):
                np.testing.assert_allclose(Operator(circuit).data,expected,atol=1e-9,rtol=0)
            metrics[name]=dict(logical_gates=len(raw.data),logical_depth=raw.depth(),common_gates=len(common.data),common_depth=common.depth(),common_cx=common.count_ops().get("cx",0),build_ms=[],lower_ms=[],run_ms=[])
        for _ in range(reps):
            for name in rng.sample(list(paths),len(paths)):
                t0=time.perf_counter_ns();raw=paths[name]();t1=time.perf_counter_ns()
                common=lower(raw);t2=time.perf_counter_ns()
                out=Statevector(v).evolve(raw).data;t3=time.perf_counter_ns()
                np.testing.assert_allclose(out,expected@v,atol=1e-9,rtol=0)
                np.testing.assert_allclose(Operator(common).data,expected,atol=1e-9,rtol=0)
                for key,a,b in zip(("build_ms","lower_ms","run_ms"),(t0,t1,t2),(t1,t2,t3),strict=True):
                    metrics[name][key].append((b-a)/1e6)
        for result in metrics.values():
            for key in ("build_ms","lower_ms","run_ms"):result[key]=stats(result[key])
        rows.append(dict(kind=kind,n=n,index=index,seed=seed,paths=metrics))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=5);a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps({"scope":"authored research; parity baseline includes SDK export; no runtime promotion","rows":[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]},indent=2,allow_nan=False))
