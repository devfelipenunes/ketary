"""Combined C API + QuEST research pipeline, no public backend change."""
import argparse
import json
import os
from pathlib import Path
import numpy as np
import ketary as q
from ketary._result import Result
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.circuit import Parameter,Gate
from longitudinal_benchmark import paired
from quest_probe import QuestProbe,pack,OPCODES
from native_execution_benchmark import circuit
import _ketary_capi_probe as capi

def rust_pack(c):
    if not isinstance(c,QuantumCircuit) or c.metadata or getattr(c,"layout",None) is not None:
        raise ValueError("expected unannotated native logical circuit")
    n,rows,angles,phase=capi.pack_quest(c._data)
    return n,np.frombuffer(rows,dtype=np.int32).reshape(-1,3),np.frombuffer(angles,dtype=np.float64),phase

def check(quest):
    for name in OPCODES:
        c=QuantumCircuit(3,global_phase=.43)
        args=(2,0) if name in {"cx","cz","swap"} else (-.31,2) if name in {"rx","ry","rz","p"} else (1,)
        getattr(c,name)(*args)
        a,b=pack(c),rust_pack(c)
        assert a[0]==b[0] and a[3]==b[3]
        np.testing.assert_array_equal(a[1],b[1])
        np.testing.assert_array_equal(a[2],b[2])
        for state in np.eye(8,dtype=np.complex128):
            expected=Statevector(state).evolve(c).data
            np.testing.assert_allclose(quest.execute(b,state)[0],expected,atol=1e-9,rtol=0)
    circuits=[QuantumCircuit(2,1)]
    for kind in ("barrier","open","custom","unbound"):
        c=QuantumCircuit(2)
        if kind=="barrier":c.barrier()
        elif kind=="open":c.cx(0,1,ctrl_state=0)
        elif kind=="custom":c.append(Gate("h",1,[]),[0])
        else:c.rx(Parameter("theta"),0)
        circuits.append(c)
    for c in circuits:
        try:rust_pack(c)
        except ValueError:pass
        else:raise AssertionError("unsupported native operation accepted")

def run(quest,reps):
    check(quest)
    cases=[]
    for n,count in ((4,100),(8,1000),(12,256),(16,256),(20,64)):
        c=circuit(n,count,1101+n)
        sdk=q.from_qiskit(c)
        rng=np.random.default_rng(1101+n)
        state=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);state/=np.linalg.norm(state)
        expected=Statevector(state).evolve(c).data
        def execute(packer):
            return Result(quest.execute(packer(c),state)[0]).math.statevector()
        prepared=rust_pack(c)
        funcs={"native":lambda:Statevector(state).evolve(c).data.copy(),
               "ketary":lambda:sdk.run(initial_state=state).math.statevector(),
               "quest_python_pack":lambda:execute(pack),
               "quest_rust_pack":lambda:execute(rust_pack),
               "quest_prepared":lambda:Result(quest.execute(prepared,state)[0]).math.statevector()}
        for name,fn in funcs.items():
            np.testing.assert_allclose(fn(),expected,atol=1e-9,rtol=0,err_msg=name)
        row={"case":"execute","n":n,"gates":count,**paired(funcs,reps,1101+n)}
        cases.append(row)
    for count in (1000,10000,100000):
        c=circuit(8,count,2202)
        a,b=pack(c),rust_pack(c)
        assert a[0]==b[0] and a[3]==b[3]
        np.testing.assert_array_equal(a[1],b[1]);np.testing.assert_array_equal(a[2],b[2])
        cases.append({"case":"pack","gates":count,**paired({"native":lambda:pack(c),"rust_pack":lambda:rust_pack(c)},reps,2202)})
    for x in cases:
        print(json.dumps({"case":x["case"],"n":x.get("n"),"gates":x["gates"],"medians_ms":{
            k:v["median_ms"] for k,v in x["samples"].items()}}),flush=True)
    return {"scope":"research subset, single runner, full native phase comparison","cases":cases}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--library",type=Path,required=True)
    p.add_argument("--repetitions",type=int,default=30)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if not 3<=a.repetitions<=100 or os.environ.get("OMP_NUM_THREADS")!="1":
        p.error("3..100 repetitions, OMP_NUM_THREADS=1 required")
    quest=QuestProbe(a.library,1)
    try:a.output.write_text(json.dumps(run(quest,a.repetitions),indent=2,allow_nan=False))
    finally:quest.close()
