"""Matched diagnostics for the official Qiskit C ABI; research only."""
import json
import random
import sys
import argparse
import numpy as np
import ketary as q
import qiskit
from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.quantum_info import Operator
import _ketary_capi_probe as capi
from longitudinal_benchmark import paired

NAMES=("h","x","z","rx","ry","rz","cx","cz")
def workload(n,count,seed):
    rng=random.Random(seed)
    rows=[];angles=[]
    for _ in range(count):
        op=rng.randrange(len(NAMES))
        w=rng.sample(range(n),2 if op>=6 else 1)
        rows.append((op,w[0],w[1] if len(w)==2 else -1))
        angles.append(rng.uniform(-3,3) if 3<=op<=5 else 0.)
    return np.array(rows,dtype=np.int32),np.array(angles,dtype=np.float64)

def build_python(n,rows,angles,sdk=False):
    c=q.Circuit(n) if sdk else QuantumCircuit(n,global_phase=.37)
    for (op,a,b),v in zip(rows,angles,strict=True):
        args=(float(v),int(a)) if 3<=op<=5 else (int(a),int(b)) if op>=6 else (int(a),)
        getattr(c,NAMES[op])(*args)
    if sdk:
        native=c.to_qiskit()
        native.global_phase=.37
        return native
    return c

def pack_python(c):
    rows=[];angles=[]
    for entry in c.data:
        op=NAMES.index(entry.operation.name)
        w=[c.find_bit(v).index for v in entry.qubits]
        rows.append((op,w[0],w[1] if len(w)==2 else -1))
        angles.append(float(entry.operation.params[0]) if 3<=op<=5 else 0.)
    return c.num_qubits,np.array(rows,dtype=np.int32).tobytes(),np.array(angles,dtype=np.float64).tobytes(),float(c.global_phase)

def check():
    rows,angles=workload(3,64,42)
    native=build_python(3,rows,angles)
    other=capi.build(3,rows.tobytes(),angles.tobytes(),.37)
    assert native==other
    np.testing.assert_allclose(Operator(native).data,Operator(other).data,atol=1e-12,rtol=0)
    assert pack_python(native)==capi.pack(native._data)
    assert capi.pack(other._data)==capi.pack(native._data)
    for c in [QuantumCircuit(2,1), QuantumCircuit(2)]:
        if not c.num_clbits: c.append(Gate("h",1,[]),[0])
        try: capi.pack(c._data)
        except ValueError: pass
        else: raise AssertionError("unsupported circuit accepted")
    for row in [(8,0,-1),(0,3,-1),(6,0,0),(0,0,1)]:
        try: capi.build(3,np.array([row],dtype=np.int32).tobytes(),np.zeros(1).tobytes(),0.)
        except ValueError: pass
        else: raise AssertionError("invalid gate accepted")

def run(reps):
    check()
    cases=[]
    for count in (1000,10000,100000):
        n=8
        rows,angles=workload(n,count,43+count)
        # Both Python paths consume arrays; C path includes bytes conversion.
        native=build_python(n,rows,angles)
        funcs={"native":lambda:build_python(n,rows,angles),
               "ketary":lambda:build_python(n,rows,angles,True),
               "capi":lambda:capi.build(n,rows.tobytes(),angles.tobytes(),.37)}
        assert all(fn()==native for fn in funcs.values())
        data=paired(funcs,reps,42)
        cases.append({"case":"build","gates":count,**data})
        f={"native":lambda:pack_python(native),"capi":lambda:capi.pack(native._data)}
        assert f["native"]()==f["capi"]()
        data=paired(f,reps,43)
        cases.append({"case":"pack","gates":count,**data})
    for c in cases:
        print(json.dumps({"case":c["case"],"gates":c["gates"],"medians_ms":{
            k:v["median_ms"] for k,v in c["samples"].items()}}),file=sys.stderr)
    return {"scope":"shared CI; identical native circuits; experimental C API","qiskit":qiskit.__version__,"cases":cases}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--repetitions",type=int,default=30)
    a=p.parse_args()
    if not 3<=a.repetitions<=100: p.error("3..100 repetitions")
    print(json.dumps(run(a.repetitions),indent=2))
