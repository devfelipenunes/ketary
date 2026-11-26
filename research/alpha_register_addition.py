"""Bounded reversible addition: |a,b> -> |a,b+a mod 2**n>.

No carry output, hidden work bits, measurement, reset or public API.
"""
import argparse
import inspect
import json
import random
import time
import numpy as np
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit.circuit.library import ModularAdderGate
from qiskit.quantum_info import Operator,Statevector
from research.circuit_rewrite_ladder import metrics,stats

def sdk_add(n):
    if type(n) is not int or not 1<=n<=3:
        raise ValueError("bounded research width 1..3")
    c=q.Circuit(2*n)
    for a in range(n):
        for target in reversed(range(a,n)):
            controls=[a,*range(n+a,n+target)]
            if len(controls)==1:c.cx(controls[0],n+target)
            elif len(controls)==2:c.ccx(*controls,n+target)
            else:c.mcx(controls,n+target)
    return c

def native_add(n):
    c=QuantumCircuit(2*n)
    c.append(ModularAdderGate(n),range(2*n))
    return c

def reference(n):
    N=1<<n
    mapping=[(i%N)+N*((i//N+i%N)%N) for i in range(N*N)]
    expected=np.zeros((N*N,N*N),complex)
    expected[mapping,np.arange(N*N)]=1
    return expected

def run(seed,reps=5):
    rng=np.random.default_rng(seed);order=random.Random(seed);rows=[]
    for n in (1,2,3):
        expected=reference(n)
        v=rng.normal(size=len(expected))+1j*rng.normal(size=len(expected))
        v/=np.linalg.norm(v)
        builders={"ketary":sdk_add,"native_library":native_add}
        data={}
        for route,build in builders.items():
            c=build(n);raw=c.to_qiskit() if route=="ketary" else c
            common=transpile(raw,basis_gates=["u","cx"],optimization_level=0,seed_transpiler=seed,qubits_initially_zero=False)
            for actual in (raw,common):
                np.testing.assert_allclose(Operator(actual).data,expected,atol=1e-9,rtol=0)
            np.testing.assert_allclose(Operator(raw.inverse()).data,expected.conj().T,atol=1e-9,rtol=0)
            source=inspect.getsource(build)
            data[route]=dict(source=source,metrics=metrics(source),logical_gates=len(raw.data),common_gates=len(common.data),common_cx=int(common.count_ops().get("cx",0)),common_depth=common.depth(),build=[],run=[])
        for _ in range(reps):
            for route in order.sample(list(builders),len(builders)):
                start=time.perf_counter_ns();c=builders[route](n);mid=time.perf_counter_ns()
                out=c.run(initial_state=v).math.statevector() if route=="ketary" else Statevector(v).evolve(c).data.copy()
                end=time.perf_counter_ns()
                np.testing.assert_allclose(out,expected@v,atol=1e-9,rtol=0)
                data[route]["build"].append((mid-start)/1e6)
                data[route]["run"].append((end-mid)/1e6)
        for r in data.values():
            for key in ("build","run"):r[key]=stats(r[key])
        rows.append(dict(n=n,seed=seed,state_payload_bytes=v.nbytes,operator_payload_bytes=expected.nbytes,paths=data))
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--reps",type=int,default=5);a=p.parse_args()
    if a.reps<1:p.error("positive reps required")
    print(json.dumps(dict(scope="full ancilla-free modular addition, native library comparison; source includes factory call but not library implementation; build excludes lowering",rows=[r for seed in (1101,2202,3303) for r in run(seed,a.reps)]),indent=2,allow_nan=False))
