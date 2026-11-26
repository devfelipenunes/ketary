"""Native extended coverage and copy/translation ablation with strict oracles."""
import argparse
import json
import os
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit,transpile
from qiskit.circuit import Gate,Parameter
from qiskit.quantum_info import Statevector,Operator
from ketary._result import Result
from algorithm_matrix import catalog, state_for, verify_vector, verify_circuit, lower
from quest_extended_probe import Extended,python_pack,rust_pack,freeze,NAMES
from longitudinal_benchmark import paired

def reject(fn):
    try:fn()
    except (ValueError,RuntimeError,TypeError):return
    raise AssertionError("invalid case accepted")

def compare_packs(a,b):
    assert a[0]==b[0] and a[3]==b[3]
    np.testing.assert_array_equal(a[1],b[1])
    np.testing.assert_array_equal(a[2],b[2])

def regression(engine):
    for name in NAMES:
        c=QuantumCircuit(5,global_phase=.73)
        if name=="mcx":c.mcx([4,0,2],1)
        elif name=="ccx":c.ccx(4,0,2)
        elif name in ("cp","rzz"):getattr(c,name)(-3.7,4,1)
        elif name in ("cx","cz","swap"):getattr(c,name)(4,1)
        elif name in ("rx","ry","rz","p"):getattr(c,name)(-3.7,4)
        else:getattr(c,name)(4)
        p=freeze(python_pack(c))
        if name!="mcx":compare_packs(p,rust_pack(c))
        else:reject(lambda:rust_pack(c))
        op=Operator(c).data
        for i,v in enumerate(np.eye(32,dtype=np.complex128)):
            verify_vector(op[:,i],engine.run(p,v)[0])
        v=state_for(5,1101);saved=v.copy()
        expected=Statevector(v).evolve(c).data
        verify_vector(expected,engine.snapshot(p,v).math.statevector())
        np.testing.assert_array_equal(v,saved)
        snap=engine.snapshot(p,v)
        exported=snap.math.statevector();exported[:]=0
        verify_vector(expected,snap.math.statevector())
        c.x(3);verify_vector(expected,engine.run(p,v)[0])
        reject(lambda:p[1].setflags(write=True))
        reject(lambda:p[2].setflags(write=True))
        table=np.stack([p[2]]*3)
        out,_=engine.run(p,v,table)
        for row in out:verify_vector(expected,row)
        out[0,:]=0;verify_vector(expected,out[1])
    for label in ("open","custom","symbolic","classical","barrier","metadata"):
        c=QuantumCircuit(4,1) if label=="classical" else QuantumCircuit(4)
        if label=="open":c.cp(.2,0,1,ctrl_state=0)
        elif label=="custom":c.append(Gate("rzz",2,[.2]),[0,1])
        elif label=="symbolic":c.rx(Parameter("x"),0)
        elif label=="classical":c.measure(0,0)
        elif label=="barrier":c.barrier()
        else:c.metadata={"tag":"unsupported"}
        reject(lambda:python_pack(c));reject(lambda:rust_pack(c))
    c=QuantumCircuit(5);c.mcx([4,0,2],1)
    p=python_pack(c);v=state_for(5,1200)
    bad=p[1].copy();bad[0,3]=bad[0,2]
    reject(lambda:engine.run((5,bad,p[2],p[3]),v))
    reject(lambda:engine.run(p,v*2))
    reject(lambda:engine.run(p,v,np.zeros((257,1))))
    # Distinguish CP from CRZ and RZZ from controlled phase, including phase.
    return "15 full-operator gate cases, explicit negative and ownership controls"

def workload(n,name):
    c=QuantumCircuit(n,global_phase=.41)
    rng=np.random.default_rng(n+1200)
    for i in range(24):
        wires=rng.choice(n,4,replace=False).tolist()
        t=float(rng.uniform(-4,4))
        if name=="cp":c.cp(t,*wires[:2])
        elif name=="rzz":c.rzz(t,*wires[:2])
        elif name=="ccx":c.ccx(*wires[:3])
        else:c.mcx(wires[:3],wires[3])
    return c

def trial(engine,c,name,reps,seed):
    direct=freeze(python_pack(c));normalized=lower(c,seed)
    verify_circuit(c,normalized)
    lowered=freeze(rust_pack(normalized))
    v=state_for(c.num_qubits,seed)
    def native():return Statevector(v).evolve(c).data.copy()
    def copied(p):return Result(engine.run(p,v)[0]).math.statevector()
    def adopted(p):return engine.snapshot(p,v).math.statevector()
    funcs={"native":native,"direct_python_pack":lambda:adopted(python_pack(c)),
           "direct_prepared_copy":lambda:copied(direct),
           "direct_prepared_adopt":lambda:adopted(direct),
           "lowered_prepared_adopt":lambda:adopted(lowered),
           "forced_lower_pack_adopt":lambda:adopted(rust_pack(lower(c,seed)))}
    try:
        rp=rust_pack(c)
    except ValueError:
        rust_status="REJECTED"
    else:
        compare_packs(direct,rp);rust_status="SUPPORTED"
        funcs["direct_rust_pack"]=lambda:adopted(rust_pack(c))
    expected=native()
    errors={k:verify_vector(expected,fn()) for k,fn in funcs.items()}
    sample=paired(funcs,reps,seed)
    # Copy vs adoption use a fresh private native output for both paths.
    table=np.stack([direct[2]]*4)
    if table.nbytes<=64*1024**2:
        def repeated():return np.stack([engine.run(direct,v)[0] for _ in range(4)])
        def batch():return engine.run(direct,v,table)[0]
        out,t=engine.run(direct,v,table)
        for x in out:verify_vector(expected,x)
        np.testing.assert_allclose(repeated(),batch(),atol=1e-9,rtol=0)
        bs=paired({"native":repeated,"batch":batch},reps,seed+1)
    else:t=None;bs=None
    result={"name":name,"n":c.num_qubits,"original_gates":len(c.data),
            "lowered_gates":len(normalized.data),"rust_direct":rust_status,
            "state_bytes":v.nbytes,"extended_topology_bytes":direct[1].nbytes,
            "validation":errors,"batch_stage_names":["allocation","input","kernel","export","destroy"],
            "batch_stage_example_ms":t.tolist() if t is not None else None,
            "batch_comparison":bs,**sample}
    print(json.dumps({k:result[k] for k in ("name","n","original_gates","lowered_gates","rust_direct","validation")}|
        {"medians_ms":{k:x["median_ms"] for k,x in sample["samples"].items()},
         "batch_medians_ms":{k:x["median_ms"] for k,x in bs["samples"].items()} if bs else None}),flush=True)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--library",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--repetitions",type=int,default=10)
    p.add_argument("--seed",type=int,default=1101)
    p.add_argument("--widths",type=int,nargs="+",default=[4,8,12])
    a=p.parse_args()
    if not 3<=a.repetitions<=100 or not all(4<=n<=16 for n in a.widths) or os.getenv("OMP_NUM_THREADS")!="1":
        p.error("bounded single-thread comparison")
    engine=Extended(a.library)
    try:
        proof=regression(engine);rows=[]
        for n in a.widths:
            for name in ("cp","rzz","ccx","mcx"):
                rows.append(trial(engine,workload(n,name),name,a.repetitions,a.seed))
        for name,family,n,native,_ in catalog("algorithms",a.seed,False):
            if n not in a.widths or family not in ("qft","qaoa","grover","phase_estimation","trotter"):continue
            c=native()
            try:python_pack(c)
            except ValueError as exc:
                rows.append({"name":name,"status":"DIRECT_REJECTED","reason":str(exc)})
                continue
            rows.append(trial(engine,c,name,a.repetitions,a.seed))
        a.output.write_text(json.dumps({"scope":"research CPU, matched direct/decomposed, no silent fallback",
            "seed":a.seed,"repetitions":a.repetitions,"regression":proof,"rows":rows},indent=2,allow_nan=False))
    finally:engine.close()
if __name__=="__main__":main()
