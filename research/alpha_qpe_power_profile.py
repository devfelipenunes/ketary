"""Known phase QPE: matched full operators, off-grid distributions and cost."""
import argparse
import json
import random
import time
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import PhaseGate, QFTGate
from qiskit.quantum_info import Operator, Statevector
import ketary as q
from research.circuit_rewrite_ladder import stats

def manual(p,m):
    c=QuantumCircuit(m+1);c.x(m);c.h(range(m))
    for k in range(m):c.cp(2*np.pi*((p*(1<<k))%1),k,m)
    c.append(QFTGate(m).inverse(),range(m))
    return c

def powers(p,m):
    c=QuantumCircuit(m+1);c.x(m);c.h(range(m))
    for k in range(m):
        c.append(PhaseGate(2*np.pi*p).power(1<<k).control(1),[k,m])
    c.append(QFTGate(m).inverse(),range(m))
    return c

def run(seed,reps):
    rng=random.Random(seed)
    rows=[]
    for m in (2,3,5):
        N=1<<m
        for p in (3/8,.237,0.):
            paths={"ketary":lambda:q.phase_estimation(p,precision=m).to_qiskit(),
                   "manual_cp":lambda:manual(p,m),"native_power":lambda:powers(p,m)}
            indices=np.arange(N)
            expected=np.abs(np.exp(2j*np.pi*(p-indices[:,None]/N)*indices[None,:]).mean(axis=1))**2
            reference=Operator(manual(p,m)).data
            results={}
            for name,fn in paths.items():
                raw=fn();common=transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=seed,qubits_initially_zero=False)
                for c in (raw,common):
                    np.testing.assert_allclose(Operator(c).data,reference,atol=1e-9,rtol=0)
                v=Statevector.from_instruction(raw).data
                np.testing.assert_allclose(abs(v[N:])**2,expected,atol=1e-9,rtol=0)
                np.testing.assert_allclose(v[:N],0.,atol=1e-9,rtol=0)
                results[name]=dict(common_gates=len(common.data),common_cx=common.count_ops().get("cx",0),build_ms=[])
            for _ in range(reps):
                for name in rng.sample(list(paths),len(paths)):
                    t=time.perf_counter_ns();raw=paths[name]();dt=(time.perf_counter_ns()-t)/1e6
                    np.testing.assert_allclose(Operator(raw).data,reference,atol=1e-9,rtol=0)
                    results[name]["build_ms"].append(dt)
            for x in results.values():x["build_ms"]=stats(x["build_ms"])
            rows.append(dict(precision=m,phase=p,seed=seed,paths=results))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=9);a=p.parse_args()
    if a.reps<1:p.error("positive repetitions required")
    print(json.dumps({"scope":"known phase only; construction includes Ketary export; no generic QPE guarantee","rows":[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]},indent=2,allow_nan=False))
