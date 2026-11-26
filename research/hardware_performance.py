"""Explicit hardware diagnostics. No GPU/MPI claim without actual execution."""
import argparse
import json
import os
import platform
import random
import statistics
import struct
import subprocess
import tempfile
import time
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

NAMES=("h","x","y","z","rx","ry","rz","cx","cz","swap","p")
def make(n,count,seed,family):
    rng=random.Random(seed)
    c=QuantumCircuit(n,global_phase=.37)
    rows=[];angles=[]
    for i in range(count):
        op=rng.choice([3,6,8,10] if family=="diagonal" else list(range(len(NAMES))))
        wires=rng.sample(range(n),2 if op in (7,8,9) else 1)
        theta=rng.uniform(-3,3) if op in (4,5,6,10) else 0.
        args=(theta,*wires) if op in (4,5,6,10) else tuple(wires)
        getattr(c,NAMES[op])(*args)
        rows.append([op,wires[0],wires[1] if len(wires)==2 else -1])
        angles.append(theta)
    rg=np.random.default_rng(seed+n)
    state=rg.normal(size=1<<n)+1j*rg.normal(size=1<<n)
    state/=np.linalg.norm(state)
    return c,np.array(rows,dtype=np.int32),np.array(angles,dtype=np.float64),state

def describe(x):
    return {"median_ms":statistics.median(x),"p95_ms":float(np.percentile(x,95)),"raw_ms":x}

def quest(exe,mode,threads,ranks,reps,reuse,c,rows,angles,state,expected):
    with tempfile.TemporaryDirectory() as tmp:
        src=Path(tmp)/"in.bin";dst=Path(tmp)/"out.bin"
        src.write_bytes(struct.pack("=iid",c.num_qubits,len(rows),float(c.global_phase))+
                        rows.tobytes()+angles.tobytes()+state.tobytes())
        command=[str(exe.resolve()),str(src),str(dst),mode,str(threads),str(reps),str(int(reuse))]
        if mode=="mpi": command=["mpiexec","-n",str(ranks),*command]
        env={**os.environ,"OMP_NUM_THREADS":str(threads),"OPENBLAS_NUM_THREADS":"1","MKL_NUM_THREADS":"1"}
        t=time.perf_counter_ns()
        p=subprocess.run(command,env=env,check=True,capture_output=True,text=True,timeout=600)
        wall=(time.perf_counter_ns()-t)/1e6
        measured=[]
        for line in p.stdout.splitlines():
            try:
                v=[float(x) for x in line.split(",")]
                if len(v)==3: measured.append(v)
            except ValueError: pass
        if len(measured)!=reps: raise RuntimeError(f"unexpected timing output: {p.stdout}")
        out=np.fromfile(dst,dtype=np.complex128)
        np.testing.assert_allclose(out,expected,atol=1e-9,rtol=0)
        arr=np.asarray(measured)
        return {"reuse":reuse,"threads":threads,"ranks":ranks,
                "max_error":float(np.max(np.abs(out-expected))),"process_wall_ms":wall,
                "initialization":describe(arr[:,0].tolist()),"kernel":describe(arr[:,1].tolist()),
                "export":describe(arr[:,2].tolist()),"cycle":describe(arr.sum(axis=1).tolist())}

def aer(c,state,expected,threads,reps,fusion):
    sim=AerSimulator(method="statevector",device="CPU",precision="double",
        max_parallel_threads=threads,max_parallel_experiments=1,max_parallel_shots=1,
        statevector_parallel_threshold=1,fusion_enable=fusion)
    work=QuantumCircuit(c.num_qubits)
    work.set_statevector(state);work.compose(c,inplace=True)
    phase=float(work.global_phase);work.global_phase=0.;work.save_statevector()
    times=[]
    for i in range(reps+3):
        t=time.perf_counter_ns()
        result=sim.run(work,shots=1).result()
        if not result.success: raise RuntimeError(result.status)
        out=np.array(result.data(0)["statevector"],dtype=np.complex128,copy=True)*np.exp(1j*phase)
        dt=(time.perf_counter_ns()-t)/1e6
        np.testing.assert_allclose(out,expected,atol=1e-9,rtol=0)
        if i>=3:times.append(dt)
    return {"fusion":fusion,"threads":threads,"max_error":float(np.max(np.abs(out-expected))),
            "prepared_end_to_end":describe(times)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--exe",type=Path,required=True)
    p.add_argument("--mode",choices=["cpu","gpu","mpi"],required=True)
    p.add_argument("--threads",type=int,nargs="+",default=[1,2,4])
    p.add_argument("--ranks",type=int,default=2)
    p.add_argument("--repetitions",type=int,default=30)
    p.add_argument("--widths",type=int,nargs="+",default=[8,12,18,20])
    p.add_argument("--label",required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--aer",action="store_true")
    a=p.parse_args()
    if not 3<=a.repetitions<=100 or not all(2<=n<=22 for n in a.widths):
        p.error("invalid width or repetitions")
    affinity=sorted(os.sched_getaffinity(0))
    if any(t<1 or t>len(affinity) for t in a.threads): p.error("thread count exceeds affinity")
    if a.mode=="mpi" and (a.ranks<2 or a.ranks*max(a.threads)>len(affinity)):
        p.error("rank x thread count exceeds local affinity")
    cases=[]
    for n in a.widths:
        for family in ("mixed","diagonal"):
            c,rows,angles,state=make(n,128,1101+n,family)
            expected=Statevector(state).evolve(c).data
            trials=[(t,reuse) for t in a.threads for reuse in (False,True)]
            random.Random(2701+n).shuffle(trials)
            qrows=[quest(a.exe,a.mode,t,a.ranks if a.mode=="mpi" else 1,a.repetitions,
                         reuse,c,rows,angles,state,expected) for t,reuse in trials]
            arows=[]
            if a.aer:
                pairs=[(t,fusion) for t in a.threads for fusion in (False,True)]
                random.Random(2702+n).shuffle(pairs)
                arows=[aer(c,state,expected,t,a.repetitions,fusion) for t,fusion in pairs]
            row={"n":n,"gates":len(rows),"family":family,"quest":qrows,"aer":arows}
            cases.append(row)
            print(json.dumps({"n":n,"family":family,"quest_ms":[
                {"threads":x["threads"],"reuse":x["reuse"],"cycle":x["cycle"]["median_ms"]} for x in qrows],
                "aer_ms":[{"threads":x["threads"],"fusion":x["fusion"],"total":x["prepared_end_to_end"]["median_ms"]} for x in arows]}),flush=True)
    a.output.write_text(json.dumps({"scope":"same-host diagnostics; native cycle excludes process launch",
        "label":a.label,"mode":a.mode,"affinity":affinity,"platform":platform.platform(),
        "repetitions":a.repetitions,"cases":cases},indent=2,allow_nan=False))

if __name__=="__main__":main()
