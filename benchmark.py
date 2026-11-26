"""Paired diagnostic benchmark; not a release gate on shared CI hardware."""
import argparse
import json
import os
import platform
import random
import resource
import statistics
import subprocess
import sys
import time
import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import ketary as q

def workload(n, count):
    rng=random.Random(20261125+n+count)
    ops=[]
    for _ in range(count):
        name=rng.choice(("h","x","z","cx","swap"))
        wires=tuple(rng.sample(range(n),2 if name in ("cx","swap") else 1))
        ops.append((name,wires))
    return ops

def mixed_workload(n,count):
    rng=random.Random(112026+n+count)
    ops=[]
    arity={"h":1,"x":1,"y":1,"z":1,"s":1,"t":1,"rx":1,"ry":1,"rz":1,"cx":2,"cz":2,"swap":2,"ccx":3}
    for _ in range(count):
        name=rng.choice(tuple(arity))
        wires=tuple(rng.sample(range(n),arity[name]))
        args=(rng.uniform(-3,3),*wires) if name in ("rx","ry","rz") else wires
        ops.append((name,args))
    return ops

def build(n, ops, variant):
    c=QuantumCircuit(n) if variant=="native" else q.Circuit(n)
    gates=c if variant=="native" else c.gates
    for name,wires in ops:
        getattr(gates,name)(*wires)
    return c

def execute(c,variant):
    # Both return an independent complex128 vector. Ketary additionally validates
    # normalization and preserves an independent Result; report this extra work.
    return Statevector.from_instruction(c).data.copy() if variant=="native" else c.run().math.statevector()

def summarize(values):
    return {"median_ms":statistics.median(values),"p95_ms":float(np.percentile(values,95)),"raw_ms":values}

def paired(native,sdk,reps):
    functions={"native":native,"sdk":sdk}
    samples={k:[] for k in functions}
    rng=random.Random(42)
    for i in range(reps+3):
        order=list(functions); rng.shuffle(order)
        for label in order:
            t=time.perf_counter_ns(); result=functions[label](); elapsed=(time.perf_counter_ns()-t)/1e6
            del result
            if i>=3: samples[label].append(elapsed)
    a,b=(summarize(samples[k]) for k in ("native","sdk"))
    return {"native":a,"sdk":b,"overhead_percent":100*(b["median_ms"]/a["median_ms"]-1),"delta_ms":b["median_ms"]-a["median_ms"]}

def memory_kib():
    # Linux /proc VmHWM is the process image high-water mark, avoiding
    # ru_maxrss inheritance from the benchmark coordinator across fork/exec.
    if sys.platform.startswith("linux"):
        with open("/proc/self/status",encoding="utf-8") as f:
            fields={line.split(":",1)[0]:line.split(":",1)[1].strip() for line in f if ":" in line}
        return {"current_kib":int(fields["VmRSS"].split()[0]),"peak_kib":int(fields["VmHWM"].split()[0]),"source":"procfs"}
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"current_kib":None,"peak_kib":peak/1024 if sys.platform=="darwin" else peak,"source":"getrusage"}

def rss_worker(variant):
    n=20; ops=[("h",(0,)),("cx",(0,n-1)),("z",(n-1,))]
    c=build(n,ops,variant); before=memory_kib()
    state=execute(c,variant)
    after=memory_kib()
    assert np.count_nonzero(abs(state)>1e-12)==2
    assert np.isclose(np.linalg.norm(state),1)
    return {"variant":variant,"n":n,"gates":len(ops),"before":before,"after":after,"payload_bytes":state.nbytes}

def main(reps):
    data={"commit":os.environ.get("GITHUB_SHA","local-unrecorded"),"threads":{k:os.environ.get(k) for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS")},"affinity":sorted(os.sched_getaffinity(0)) if hasattr(os,"sched_getaffinity") else None,"cpu_count":os.cpu_count(),"python":sys.version,"platform":platform.platform(),"qiskit":qiskit.__version__,"numpy":np.__version__,"cpu":platform.processor(),"repetitions":reps,"cases":[],"rss":[]}
    for n,count in [(8,1000),(8,10000)]:
        ops=workload(n,count)
        native=build(n,ops,"native"); sdk=build(n,ops,"sdk")
        assert native==sdk.to_qiskit()
        result=paired(lambda:build(n,ops,"native"),lambda:build(n,ops,"sdk"),reps)
        data["cases"].append({"operation":"build","n":n,"gates":count,**result})
    for n,count in [(8,128),(12,128),(16,64)]:
        ops=workload(n,count)
        native=build(n,ops,"native"); sdk=build(n,ops,"sdk")
        np.testing.assert_allclose(execute(native,"native"),execute(sdk,"sdk"),atol=1e-9,rtol=0)
        result=paired(lambda:execute(native,"native"),lambda:execute(sdk,"sdk"),reps)
        data["cases"].append({"operation":"statevector","n":n,"gates":count,**result})
    # Supplemental operations: compare matching outputs, not different semantics.
    n=8; ops=workload(n,128)
    native=build(n,ops,"native"); sdk=build(n,ops,"sdk")
    for operation,base,trial in [
        ("compose",lambda:native.compose(native),lambda:sdk.compose(sdk)),
        ("export_copy",lambda:native.copy(),lambda:sdk.to_qiskit()),
    ]:
        expected=base(); observed=trial()
        assert expected==(observed.to_qiskit() if isinstance(observed,q.Circuit) else observed)
        data["cases"].append({"operation":operation,"n":n,"gates":len(ops),**paired(base,trial,reps)})
    def native_trace():
        initial=np.zeros(1<<n,dtype=complex)
        initial[0]=np.exp(1j*float(native.global_phase))
        state=Statevector(initial)
        snapshots=[state.data.copy()]
        for item in native.data:
            state=state.evolve(item.operation,qargs=[native.find_bit(w).index for w in item.qubits])
            snapshots.append(state.data.copy())
        return tuple(snapshots)
    def sdk_trace():
        return tuple(step.result.math.statevector() for step in sdk.debug.trace())
    for expected,observed in zip(native_trace(),sdk_trace(),strict=True):
        np.testing.assert_allclose(expected,observed,atol=1e-9,rtol=0)
    data["cases"].append({"operation":"trace","n":n,"gates":len(ops),**paired(native_trace,sdk_trace,reps)})
    for n,count in [(8,1000),(8,10000)]:
        ops=mixed_workload(n,count)
        a=build(n,ops,"native"); b=build(n,ops,"sdk")
        assert a==b.to_qiskit()
        data["cases"].append({"operation":"mixed_build","n":n,"gates":count,**paired(lambda:build(n,ops,"native"),lambda:build(n,ops,"sdk"),reps)})
        assert a.compose(a)==b.compose(b).to_qiskit()
        data["cases"].append({"operation":"mixed_compose","n":n,"gates":count,**paired(lambda:a.compose(a),lambda:b.compose(b),reps)})
    for n,count in [(8,128),(12,128)]:
        ops=mixed_workload(n,count)
        a=build(n,ops,"native"); b=build(n,ops,"sdk")
        np.testing.assert_allclose(execute(a,"native"),execute(b,"sdk"),atol=1e-9,rtol=0)
        data["cases"].append({"operation":"mixed_statevector","n":n,"gates":count,**paired(lambda:execute(a,"native"),lambda:execute(b,"sdk"),reps)})
    # Matched snapshot queries, separate from circuit construction/execution.
    from qiskit.quantum_info import partial_trace,Pauli
    native=Statevector.from_instruction(q.ghz(8).to_qiskit())
    sdk=q.ghz(8).run()
    native_density=lambda:partial_trace(native,list(range(1,8))).data.copy()
    sdk_density=lambda:sdk.math.density_matrix([0])
    np.testing.assert_allclose(native_density(),sdk_density(),atol=1e-9,rtol=0)
    data["cases"].append({"operation":"reduced_density","n":8,"gates":8,**paired(native_density,sdk_density,reps)})
    pauli="X"*8
    native_pauli=lambda:float(native.expectation_value(Pauli(pauli)).real)
    sdk_pauli=lambda:sdk.math.expectation(pauli)
    np.testing.assert_allclose(native_pauli(),sdk_pauli(),atol=1e-9,rtol=0)
    data["cases"].append({"operation":"snapshot_pauli","n":8,"gates":8,**paired(native_pauli,sdk_pauli,reps)})
    # Same mathematical variance, not different guarantees.
    terms={"X"*8:.3,"Z"*8:.4,"Y"*8:-.2,"I"*8:1.0}
    dense=lambda:sdk.math.observable_variance(terms)
    streamed=lambda:sdk.math.observable_variance_streamed(terms)
    np.testing.assert_allclose(dense(),streamed(),atol=1e-10,rtol=0)
    data["cases"].append({"operation":"variance_dense_vs_streamed","n":8,"gates":8,
                          "native_label":"Ketary dense","sdk_label":"Ketary streamed",**paired(dense,streamed,reps)})
    ops=mixed_workload(8,1000)
    # Precompute identical operations for both variants.
    def fluent_fixed():
        c=q.Circuit(8)
        for name,args in ops:
            getattr(c,name)(*args)
        return c
    assert build(8,ops,"native")==fluent_fixed().to_qiskit()
    data["cases"].append({"operation":"fluent_build","n":8,"gates":1000,
                          **paired(lambda:build(8,ops,"native"),fluent_fixed,reps)})
    # Repeated fixed-size appends: compare equal native instruction sequences.
    # Historical copy baseline measured only at 100/1000 gates to bound CI.
    def repeated(kind,count,variant):
        c=QuantumCircuit(4) if variant=="native" else q.Circuit(4)
        block=QuantumCircuit(2); block.h(0); block.cx(0,1)
        logical=q.from_qiskit(block)
        for _ in range(count//2):
            if kind=="batch":
                if variant=="native":
                    c.h([3,0])
                elif variant=="copy_baseline":
                    candidate=c.copy()
                    candidate.h(3).h(0)
                    c=candidate
                else:
                    c.h([3,0])
            elif variant=="native":
                c.compose(block,qubits=[3,0],inplace=True)
            elif variant=="copy_baseline":
                c=c.compose(logical,wires=[3,0])
            else:
                c.apply(logical,wires=[3,0])
        return c
    for kind in ("batch","block"):
        for count in (100,1000,10000):
            expected=repeated(kind,count,"native")
            assert expected==repeated(kind,count,"sdk").to_qiskit()
            data["cases"].append({"operation":"repeated_"+kind,"n":4,"gates":count,
                **paired(lambda:repeated(kind,count,"native"),lambda:repeated(kind,count,"sdk"),reps)})
            if count<=1000:
                assert expected==repeated(kind,count,"copy_baseline").to_qiskit()
                data["cases"].append({"operation":"repeated_"+kind+"_copy_baseline","n":4,"gates":count,
                    "native_label":"historical copy path","sdk_label":"candidate append path",
                    **paired(lambda:repeated(kind,count,"copy_baseline"),lambda:repeated(kind,count,"sdk"),reps)})
    # Compare the new expression to equivalent current SDK loops.
    layer=q.Circuit(4).apply(q.bell(),wires=[0,1]).h([2,3])
    def loop_layers(count):
        c=q.Circuit(4)
        for _ in range(count):
            c.apply(layer)
        return c
    for count in (25,250,2500):
        direct=lambda:q.Circuit(4).apply(layer,times=count)
        loop=lambda:loop_layers(count)
        assert direct().to_qiskit()==loop().to_qiskit()
        data["cases"].append({"operation":"expressive_repeat","n":4,"gates":count*4,
            "native_label":"Ketary explicit loop","sdk_label":"Ketary apply times",**paired(loop,direct,reps)})
    variants=["native","sdk"]*3; random.Random(42).shuffle(variants)
    for variant in variants:
        raw=subprocess.check_output([sys.executable,__file__,"--rss-worker",variant],text=True)
        data["rss"].append(json.loads(raw))
    return data

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--repetitions",type=int,default=20)
    parser.add_argument("--rss-worker",choices=["native","sdk"])
    args=parser.parse_args()
    if args.rss_worker: result=rss_worker(args.rss_worker)
    else:
        if args.repetitions<20: parser.error("at least 20 repetitions")
        result=main(args.repetitions)
    print(json.dumps(result,indent=2))
