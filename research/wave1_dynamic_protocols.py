"""Matched local Aer protocols: source, raw latency and analytic measured scope."""
import inspect
import json
import time
import numpy as np
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit_aer import AerSimulator
from research.circuit_rewrite_ladder import metrics,stats

def teleport_sdk(theta,phi,axis):
    c=q.Circuit.classical(3,3).ry(theta,0).rz(phi,0).h(1).cx(1,2).cx(0,1).h(0)
    c.measure(0,0).measure(1,1).if_x(2,1).if_z(2,0)
    if axis=="Y":c.sdg(2)
    if axis in ("X","Y"):c.h(2)
    return c.measure(2,2)

def teleport_native(theta,phi,axis):
    c=QuantumCircuit(3,3);c.ry(theta,0);c.rz(phi,0);c.h(1);c.cx(1,2);c.cx(0,1);c.h(0)
    c.measure(0,0);c.measure(1,1)
    with c.if_test((c.clbits[1],1)):c.x(2)
    with c.if_test((c.clbits[0],1)):c.z(2)
    if axis=="Y":c.sdg(2)
    if axis in ("X","Y"):c.h(2)
    c.measure(2,2)
    return c

def dense_sdk(a,b):
    c=q.Circuit.classical(2,2).h(0).cx(0,1)
    if a:c.z(0)
    if b:c.x(0)
    return c.cx(0,1).h(0).measure(0,0).measure(1,1)

def dense_native(a,b):
    c=QuantumCircuit(2,2);c.h(0);c.cx(0,1)
    if a:c.z(0)
    if b:c.x(0)
    c.cx(0,1);c.h(0);c.measure(0,0);c.measure(1,1)
    return c

def native_counts(c,shots,seed):
    backend=AerSimulator(method="statevector",max_parallel_threads=1)
    compiled=transpile(c,backend=backend,optimization_level=0,seed_transpiler=seed)
    result=backend.run(compiled,shots=shots,seed_simulator=seed).result()
    assert result.success
    return dict(result.get_counts())

def run(reps=3,shots=2048):
    rows=[]
    cases=[("teleport",teleport_sdk,teleport_native,(theta,phi,axis))
           for theta,phi in ((.83,-1.17),(np.pi/2,np.pi/2)) for axis in ("X","Y","Z")]
    cases += [("dense",dense_sdk,dense_native,(a,b)) for a in (0,1) for b in (0,1)]
    for family,ks,ns,args in cases:
        row={"family":family,"inputs":args,"shots":shots,"paths":{}}
        for mode,fn in (("sdk",ks),("native",ns)):
            source=inspect.getsource(fn);row["paths"][mode]={"source":source,"metrics":metrics(source),"build":[],"run":[],"counts":[]}
        for i in range(reps):
            for mode,fn in ((("sdk",ks),("native",ns)) if i%2==0 else (("native",ns),("sdk",ks))):
                seed=29600+i
                start=time.perf_counter_ns();c=fn(*args);mid=time.perf_counter_ns()
                counts=c.run_shots(shots=shots,seed=seed).counts if mode=="sdk" else native_counts(c,shots,seed)
                end=time.perf_counter_ns()
                assert sum(counts.values())==shots
                if family=="dense":
                    a,b=args;assert counts=={f"{b}{a}":shots}
                else:
                    theta,phi,axis=args
                    want={"X":np.sin(theta)*np.cos(phi),"Y":np.sin(theta)*np.sin(phi),"Z":np.cos(theta)}[axis]
                    observed=sum((1 if k[0]=="0" else -1)*v for k,v in counts.items())/shots
                    assert abs(observed-want)<.13
                    for pair in ("00","01","10","11"):
                        assert abs(sum(v for k,v in counts.items() if k[1:]==pair)/shots-.25)<.07
                out=row["paths"][mode]
                out["build"].append((mid-start)/1e6);out["run"].append((end-mid)/1e6)
                out["counts"].append({"seed":seed,"values":counts})
                if i==0:
                    native=c.to_qiskit() if mode=="sdk" else c
                    out["logical_instructions"]=len(native.data)
                    out["classical_bits"]=native.num_clbits
                    out["quantum_wires"]=native.num_qubits
        for out in row["paths"].values():
            for key in ("build","run"):out[key]=stats(out[key])
        rows.append(row)
    return {"scope":"local Aer only; measured marginal and Bell outcome checks, not process tomography or fault tolerance; logical instruction counts include conditional blocks, not physical gate counts","rows":rows}

if __name__=="__main__":
    print(json.dumps(run(),indent=2))
