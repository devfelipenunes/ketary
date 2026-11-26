"""PERF14–18 research: prepared topology, batch register reuse and fusion."""
import argparse
import json
import os
import platform
import statistics
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector, Operator
from quest_probe import QuestProbe
from prepared_native import prepare, fuse
from longitudinal_benchmark import paired

TOL=1e-9

def state(n,seed):
    rng=np.random.default_rng(seed)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    return v/np.linalg.norm(v)

def verify(a,b):
    np.testing.assert_allclose(a,b,atol=TOL,rtol=0)
    np.testing.assert_allclose(np.sum(abs(b)**2,axis=-1),1,atol=TOL,rtol=0)
    return float(np.max(abs(a-b)))

def expect_failure(fn):
    try:fn()
    except (ValueError,TypeError,RuntimeError):return
    raise AssertionError("invalid input accepted")

def regression(quest):
    theta=Parameter("theta");phi=Parameter("phi")
    c=QuantumCircuit(3,global_phase=.43)
    c.h(2);c.rx(theta,0);c.cx(2,0);c.ry(phi,1);c.rz(theta,2);c.p(phi,0)
    plan=prepare(c)
    assert plan.parameters==tuple(c.parameters)
    vals=np.array([[.2,.6],[-.9,1.1],[0.,0.]])
    table=plan.angle_table(vals)
    for v in np.eye(8,dtype=np.complex128):
        refs=np.stack([Statevector(v).evolve(c.assign_parameters(dict(zip(plan.parameters,row,strict=True)))).data for row in vals])
        verify(refs,quest.execute_batch(plan.program(),v,table)[0])
    v=state(3,1200);saved=v.copy()
    expected=quest.execute_batch(plan.program(),v,table)[0]
    c.x(1);vals[:]=99
    verify(expected,quest.execute_batch(plan.program(),v,table)[0])
    np.testing.assert_array_equal(v,saved)
    expected[0,0]=100
    assert abs(quest.execute_batch(plan.program(),v,table)[0][0,0])<=1
    expect_failure(lambda:plan.ops.setflags(write=True))
    expect_failure(lambda:plan.angles.setflags(write=True))
    expect_failure(lambda:plan.angle_table([[float("nan"),0.]]))
    expect_failure(lambda:plan.angle_table([[1.]]))
    expect_failure(lambda:plan.angle_table([[0.,0.]]*257))
    expect_failure(lambda:quest.execute_batch(plan.program(),v,np.zeros((2,1))))
    expect_failure(lambda:quest.execute_batch(plan.program(),v*2,table))
    bad=plan.ops.copy();bad[0,0]=99
    expect_failure(lambda:quest.execute_batch((3,bad,plan.angles,plan.phase),v,table))
    bad=QuantumCircuit(2);bad.rx(2*theta,0)
    expect_failure(lambda:prepare(bad))
    bad=QuantumCircuit(2,global_phase=theta)
    expect_failure(lambda:prepare(bad))
    bad=QuantumCircuit(2);bad.barrier()
    expect_failure(lambda:prepare(bad))
    # full operators, including rotation phase across 2pi and directional gates
    for name in ("h","x","y","z","rx","ry","rz","p","cx","cz","swap"):
        c=QuantumCircuit(3,global_phase=.31)
        args=(2,0) if name in ("cx","cz","swap") else (3.6,1) if name in ("rx","ry","rz","p") else (1,)
        getattr(c,name)(*args);getattr(c,name)(*args)
        p=fuse(prepare(c))
        assert len(p.ops)==(1 if name in ("rx","ry","rz","p") else 0)
        for v in np.eye(8,dtype=np.complex128):
            verify(Statevector(v).evolve(c).data,quest.execute_batch(p.program(),v,p.angle_table([[]]))[0][0])
    c=QuantumCircuit(3);c.cx(0,2);c.cx(2,0)
    assert len(fuse(prepare(c)).ops)==2
    return "strict all-basis vectors, isolation, phase, malformed inputs and fusion"

def workload(n,count,family):
    c=QuantumCircuit(n,global_phase=.37)
    rng=np.random.default_rng(900+n)
    theta=Parameter("theta")
    for i in range(count):
        w=int(rng.integers(n));other=(w+1)%n
        if family=="sweep":
            c.rx(theta,w);c.cx(w,other)
        elif family=="fusion":
            c.rx(.2,w);c.rx(-.37,w);c.z(other);c.z(other)
        else:
            c.h(w);c.cx(w,other)
    return c

def run(quest,reps,widths):
    proof=regression(quest);rows=[]
    for n in widths:
        for family in ("mixed","fusion","sweep"):
            c=workload(n,32,family);plan=prepare(c)
            v=state(n,1101+n)
            for size in (1,4,16):
                if size*(1<<n)*16>128*1024**2:continue
                vals=np.linspace(-.9,.9,size).reshape(size,1) if plan.parameters else np.empty((size,0))
                table=plan.angle_table(vals)
                circuits=[c.assign_parameters(dict(zip(plan.parameters,row,strict=True))) if plan.parameters else c for row in vals]
                def native():
                    return np.stack([Statevector(v).evolve(cc).data for cc in circuits])
                def single():
                    return np.stack([quest.execute((plan.n,plan.ops,row,plan.phase),v)[0] for row in table])
                def batch():
                    return quest.execute_batch(plan.program(),v,table)[0]
                def prepare_batch():
                    p=prepare(c)
                    return quest.execute_batch(p.program(),v,p.angle_table(vals))[0]
                def native_bind():
                    return np.stack([Statevector(v).evolve(c.assign_parameters(dict(zip(plan.parameters,row,strict=True))) if plan.parameters else c).data for row in vals])
                funcs={"native":native,"native_bind_execute":native_bind,"quest_single":single,"quest_batch":batch,"quest_prepare_batch":prepare_batch}
                fp=None
                if not plan.parameters:
                    fp=fuse(plan);ft=fp.angle_table(vals)
                    funcs["quest_fused_batch"]=lambda:quest.execute_batch(fp.program(),v,ft)[0]
                    def fuse_batch():
                        f=fuse(prepare(c))
                        return quest.execute_batch(f.program(),v,f.angle_table(vals))[0]
                    funcs["quest_prepare_fuse_batch"]=fuse_batch
                ref=native()
                errors={k:verify(ref,fn()) for k,fn in funcs.items()}
                # Stage measurements are separate from end-to-end trial timings.
                stages=[]
                for _ in range(reps):
                    out,times=quest.execute_batch(plan.program(),v,table)
                    verify(ref,out);stages.append(times.tolist())
                result={"n":n,"family":family,"batch_size":size,"gates":len(plan.ops),
                        "fused_gates":len(fp.ops) if fp is not None else None,
                        "state_bytes":v.nbytes,"retained_output_bytes":ref.nbytes,
                        "angle_table_bytes":table.nbytes,"topology_bytes":plan.ops.nbytes,
                        "stage_names":["allocation","input","kernel","export","destroy"],
                        "stage_raw_ms":stages,"stage_median_ms":np.median(stages,axis=0).tolist(),
                        "errors":errors,**paired(funcs,reps,1101+n+size)}
                rows.append(result)
                print(json.dumps({k:result[k] for k in ("n","family","batch_size","gates","fused_gates","state_bytes","stage_median_ms","errors")}|{"medians_ms":{k:s["median_ms"] for k,s in result["samples"].items()}}),flush=True)
    return {"scope":"research CPU only; shared runner; no hardware counter/SIMD claim",
            "regression":proof,"platform":platform.platform(),"affinity":sorted(os.sched_getaffinity(0)),
            "rows":rows}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--library",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--repetitions",type=int,default=10)
    p.add_argument("--widths",type=int,nargs="+",default=[4,8,12,16])
    a=p.parse_args()
    if not 3<=a.repetitions<=100 or not all(2<=n<=20 for n in a.widths) or os.getenv("OMP_NUM_THREADS")!="1":
        p.error("bounded CPU single-thread benchmark only")
    quest=QuestProbe(a.library,1)
    try:a.output.write_text(json.dumps(run(quest,a.repetitions,a.widths),indent=2,allow_nan=False))
    finally:quest.close()
