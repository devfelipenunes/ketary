"""Measure existing diagonal parity reuse, not a new runtime synthesis path."""
import argparse
import json
import random
import time
import numpy as np
from qiskit import QuantumCircuit,transpile
from qiskit.circuit import Parameter
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp,Operator
import ketary as q
from research.circuit_rewrite_ladder import stats

def ladder(n,terms,t):
    native=QuantumCircuit(n)
    for label,w in sorted(terms.items()):
        active=[i for i,a in enumerate(reversed(label)) if a=="Z"]
        if not active:
            native.global_phase-=w*t
            continue
        pivot=active[-1]
        for i in active[:-1]:native.cx(i,pivot)
        native.rz(2*w*t,pivot)
        for i in reversed(active[:-1]):native.cx(i,pivot)
    return native

def library(n,terms,t):
    c=QuantumCircuit(n)
    c.append(PauliEvolutionGate(SparsePauliOp.from_list(list(terms.items())),time=t),range(n))
    return c

def run(seed,reps):
    rng=random.Random(seed)
    rows=[]
    for n in (4,5,6):
        terms={"I"*n:.17}
        for i in range(1,n-1):
            for j in range(i):
                label=["I"]*n
                for wire in (i,j,n-1):label[n-1-wire]="Z"
                terms["".join(label)]=rng.uniform(-1,1)
        H=q.Observable(terms)
        t=.37
        diagonal=np.array([sum(w*(-1)**sum((k>>(n-1-i))&1 for i,a in enumerate(label) if a=="Z")
                                   for label,w in terms.items()) for k in range(1<<n)])
        expected=np.diag(np.exp(-1j*t*diagonal))
        paths={"ketary":lambda:q.Circuit(n).evolve(H,time=t).to_qiskit(),
               "ladder":lambda:ladder(n,terms,t),"native":lambda:library(n,terms,t)}
        p=q.Circuit.parameter("t")
        symbolic=q.Circuit.symbolic(n).evolve(H,time=p)
        np.testing.assert_allclose(Operator(symbolic.bind({p:t}).to_qiskit()).data,expected,atol=1e-9,rtol=0)
        results={}
        for name,fn in paths.items():
            raw=fn()
            lowered=transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=seed,qubits_initially_zero=False)
            for c in (raw,lowered):
                np.testing.assert_allclose(Operator(c).data,expected,atol=1e-9,rtol=0)
            results[name]=dict(gates=len(lowered.data),cx=lowered.count_ops().get("cx",0),depth=lowered.depth(),build_ms=[])
        for _ in range(reps):
            for name in rng.sample(list(paths),len(paths)):
                start=time.perf_counter_ns();raw=paths[name]();end=time.perf_counter_ns()
                np.testing.assert_allclose(Operator(raw).data,expected,atol=1e-9,rtol=0)
                results[name]["build_ms"].append((end-start)/1e6)
        for result in results.values():result["build_ms"]=stats(result["build_ms"])
        rows.append(dict(n=n,seed=seed,terms=len(terms),paths=results))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=9);a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps(dict(scope="authored shared-CI build diagnostics; native library construction not lowering time",
        rows=[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]),indent=2,allow_nan=False))
