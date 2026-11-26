"""Research-only shared parity for a common local Pauli basis.

Applicable only when every nonidentity axis on each wire agrees.
General commuting Pauli operators need not satisfy this restriction.
"""
import argparse
import json
import random
import time
import numpy as np
import ketary as q
from scipy.linalg import expm
from qiskit import QuantumCircuit,transpile
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import Operator,SparsePauliOp,Statevector
from research.circuit_rewrite_ladder import stats

def shared(n,terms,t):
    axes={}
    diagonal={}
    for label,coefficient in terms.items():
        for wire,axis in enumerate(reversed(label)):
            if axis=="I":continue
            if wire in axes and axes[wire]!=axis:
                raise ValueError("common local basis required")
            axes[wire]=axis
        diagonal["".join("I" if a=="I" else "Z" for a in label)]=coefficient
    c=q.Circuit(n)
    for wire,axis in sorted(axes.items()):
        if axis=="X":c.h(wire)
        elif axis=="Y":c.sdg(wire).h(wire)
    c.evolve(q.Observable(diagonal),time=t)
    for wire,axis in reversed(sorted(axes.items())):
        if axis=="X":c.h(wire)
        elif axis=="Y":c.h(wire).s(wire)
    return c

def native(n,terms,t):
    c=QuantumCircuit(n)
    c.append(PauliEvolutionGate(SparsePauliOp.from_list(list(terms.items())),time=t),range(n))
    return c

def fixture(n,seed):
    rng=random.Random(seed)
    axes="XYZ"*((n+2)//3)
    terms={"I"*n:.17}
    for i in range(1,n-1):
        for j in range(i):
            label=["I"]*n
            for wire in (i,j,n-1):label[n-1-wire]=axes[wire]
            terms["".join(label)]=rng.uniform(-1,1)
    return terms

def run(seed,reps=5):
    rng=random.Random(seed);rows=[]
    for n in (4,5,6):
        terms=fixture(n,seed);H=q.Observable(terms);t=.37
        expected=expm(-1j*t*SparsePauliOp.from_list(list(terms.items())).to_matrix())
        gen=np.random.default_rng(seed);v=gen.normal(size=1<<n)+1j*gen.normal(size=1<<n);v/=np.linalg.norm(v)
        paths={"ketary":lambda:q.Circuit(n).evolve(H,time=t).to_qiskit(),
               "shared":lambda:shared(n,terms,t).to_qiskit(),"native":lambda:native(n,terms,t)}
        results={}
        for name,build in paths.items():
            raw=build();common=transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=seed,qubits_initially_zero=False)
            for c in (raw,common):np.testing.assert_allclose(Operator(c).data,expected,atol=1e-9,rtol=0)
            results[name]=dict(logical_gates=len(raw.data),common_gates=len(common.data),common_cx=int(common.count_ops().get("cx",0)),common_depth=common.depth(),build=[],run=[])
        for _ in range(reps):
            for name in rng.sample(list(paths),len(paths)):
                start=time.perf_counter_ns();raw=paths[name]();mid=time.perf_counter_ns()
                actual=Statevector(v).evolve(raw).data.copy();end=time.perf_counter_ns()
                np.testing.assert_allclose(actual,expected@v,atol=1e-9,rtol=0)
                results[name]["build"].append((mid-start)/1e6);results[name]["run"].append((end-mid)/1e6)
        for row in results.values():
            for k in ("build","run"):row[k]=stats(row[k])
        rows.append(dict(n=n,seed=seed,terms=len(terms),payload_bytes=v.nbytes,paths=results))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=5);a=p.parse_args()
    if a.reps<1:p.error("positive reps required")
    print(json.dumps(dict(scope="common-local-basis commuting subset; native evolution is not common-basis lowering time; no hardware or RSS claim",rows=[r for s in (1101,2202,3303) for r in run(s,a.reps)]),indent=2,allow_nan=False))
