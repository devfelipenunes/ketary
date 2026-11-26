"""Matched controlled synthesis routes, including repeated X parity and phase."""
import argparse
import json
import random
import time
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Statevector
from ketary._transpilation import _synthesize_native
from research.circuit_rewrite_ladder import stats


def source(n,wires,phase):
    c=q.Circuit(n)
    for w in wires:c.x(w)
    return c.evolve(q.I(),time=-phase)


def reference(n,wires,phase,state):
    mask=0
    for w in wires:mask^=1<<w
    dim=1<<(n+1)
    expected=np.zeros((dim,dim),complex)
    for j in range(dim):
        active=(j&1)==state
        expected[j^(mask<<1) if active else j,j]=np.exp(1j*phase) if active else 1.
    return expected


def baseline(c,state,seed):
    raw=QuantumCircuit(c.num_qubits+1)
    raw.append(c.to_qiskit().to_gate().control(1,ctrl_state=state,annotated=False),range(raw.num_qubits))
    return _synthesize_native(raw,seed=seed)


def candidate(c,state,seed):
    return c.control(controls=1,control_state=state,seed=seed)


def reduced(c,state,seed):
    # Research-only: cancellation of repeated X on each target is exact.
    # Use the original public strict control path on the equivalent source.
    raw=c.to_qiskit()
    mask=0
    for item in raw.data:
        if item.operation.name!="x":raise ValueError("X-only source required")
        mask^=1<<raw.find_bit(item.qubits[0]).index
    smaller=source(raw.num_qubits,[i for i in range(raw.num_qubits) if mask>>i&1],float(raw.global_phase))
    return candidate(smaller,state,seed)


def run(seed,reps=5):
    if reps<1:raise ValueError("positive repetitions required")
    rng=random.Random(seed);gen=np.random.default_rng(seed);rows=[]
    for n,count in ((1,0),(2,8),(4,32)):
        wires=[rng.randrange(n) for _ in range(count)]
        for state in (0,1):
            phase=.37 if state else -.71
            c=source(n,wires,phase);before=c.to_qiskit()
            expected=reference(n,wires,phase,state)
            v=gen.normal(size=len(expected))+1j*gen.normal(size=len(expected));v/=np.linalg.norm(v)
            paths={"generic":baseline,"installed":candidate,"reduced_research":reduced}
            result={}
            for name,fn in paths.items():
                raw=fn(c,state,seed).to_qiskit()
                np.testing.assert_allclose(Operator(raw).data,expected,atol=1e-9,rtol=0)
                assert all(item.operation.name in ("u","cx") for item in raw.data)
                result[name]=dict(gates=len(raw.data),cx=int(raw.count_ops().get("cx",0)),depth=raw.depth(),build_ms=[],run_ms=[])
            for _ in range(reps):
                for name in rng.sample(list(paths),len(paths)):
                    start=time.perf_counter_ns();raw=paths[name](c,state,seed).to_qiskit();mid=time.perf_counter_ns()
                    out=Statevector(v).evolve(raw).data;end=time.perf_counter_ns()
                    np.testing.assert_allclose(out,expected@v,atol=1e-9,rtol=0)
                    result[name]["build_ms"].append((mid-start)/1e6)
                    result[name]["run_ms"].append((end-mid)/1e6)
            assert c.to_qiskit()==before
            for data in result.values():
                for key in ("build_ms","run_ms"):data[key]=stats(data[key])
            rows.append(dict(seed=seed,n=n,source_gates=count,state=state,paths=result))
    return rows


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--reps",type=int,default=5);args=parser.parse_args()
    if args.reps<1:parser.error("positive repetitions required")
    print(json.dumps(dict(scope="X-only source, single control, phase strict; research-only reduced route; shared CI",rows=[row for seed in (1101,2202,3303) for row in run(seed,args.reps)]),indent=2,allow_nan=False))
