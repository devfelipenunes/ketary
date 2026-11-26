"""Longitudinal diagnostics with matched outputs, raw samples and runner replicates.

Shared runner results are not dedicated-host measurements or human outcomes.
Run from an installed checkout; no network or third-party source in the study.
"""
import argparse
import gc
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli
import ketary as q

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmark import mixed_workload, memory_kib
from research.circuit_writing_study import run as writing_study, metrics

TOL=1e-9


def describe(values):
    return {"median_ms":statistics.median(values),
            "p95_ms":float(np.percentile(values,95)),
            "min_ms":min(values),"max_ms":max(values),"raw_ms":values}


def paired(functions,reps,seed):
    rng=random.Random(seed)
    samples={name:[] for name in functions}
    orders=[]
    for i in range(reps+3):
        order=list(functions)
        rng.shuffle(order)
        if i>=3:
            orders.append(order)
        for name in order:
            start=time.perf_counter_ns()
            obj=functions[name]()
            elapsed=(time.perf_counter_ns()-start)/1e6
            del obj
            if i>=3:
                samples[name].append(elapsed)
    baseline=samples["native"]
    return {"samples":{name:describe(values) for name,values in samples.items()},
            "paired_ratio_to_native":{name:{
                "median":statistics.median([a/b for a,b in zip(values,baseline,strict=True)]),
                "p95":float(np.percentile([a/b for a,b in zip(values,baseline,strict=True)],95))}
                for name,values in samples.items()},
            "orders":orders}


def make_build(n,count):
    ops=mixed_workload(n,count)
    def build(mode):
        c=QuantumCircuit(n) if mode=="native" else q.Circuit(n)
        api=c.gates if mode=="gates" else c
        for name,args in ops:
            getattr(api,name)(*args)
        return c
    return {mode:lambda mode=mode:build(mode) for mode in ("native","gates","fluent")}


def repeat_build(count):
    native=QuantumCircuit(8)
    native.h(range(8))
    native.cx(0,1)
    native.cz(2,3)
    layer=q.Circuit(8).h(range(8)).cx(0,1).cz(2,3)
    def native_loop():
        c=QuantumCircuit(8)
        for _ in range(count):
            c.compose(native,inplace=True)
        return c
    def sdk_loop():
        c=q.Circuit(8)
        for _ in range(count):
            c.apply(layer)
        return c
    return {"native":native_loop,"sdk_loop":sdk_loop,
            "sdk_times":lambda:q.Circuit(8).apply(layer,times=count)}


def batch_build(count):
    def native():
        c=QuantumCircuit(8)
        for _ in range(count):
            c.h(range(8))
        return c
    def scalar():
        c=q.Circuit(8)
        for _ in range(count):
            for w in range(8):
                c.h(w)
        return c
    def grouped():
        c=q.Circuit(8)
        for _ in range(count):
            c.h(c.wires)
        return c
    return {"native":native,"sdk_scalar":scalar,"sdk_batch":grouped}


def pair_build(n,layers):
    pairs=q.ring(range(n))
    a,b=zip(*pairs,strict=True)
    edge=q.Circuit(2).cz(0,1)
    def native():
        c=QuantumCircuit(n)
        for _ in range(layers):
            c.cz(list(a),list(b))
        return c
    def scalar():
        c=q.Circuit(n)
        for _ in range(layers):
            for x,y in pairs:
                c.cz(x,y)
        return c
    def grouped():
        c=q.Circuit(n)
        for _ in range(layers):
            c.apply_each(edge,placements=pairs)
        return c
    def direct():
        c=q.Circuit(n)
        for _ in range(layers):
            c.cz(pairs=pairs)
        return c
    return {"native":native,"sdk_scalar":scalar,"sdk_apply_each":grouped,"sdk_pairs":direct}


def dynamic_build(layers):
    wires=list(range(8))
    bits=list(reversed(wires))
    def native():
        c=QuantumCircuit(8,8)
        for _ in range(layers):
            c.measure(wires,bits)
            c.reset(wires)
        return c
    def scalar():
        c=q.Circuit.classical(8,8)
        for _ in range(layers):
            for w,b in zip(wires,bits,strict=True):
                c.measure(w,b)
            for w in wires:
                c.reset(w)
        return c
    def grouped():
        c=q.Circuit.classical(8,8)
        for _ in range(layers):
            c.measure(wires,bits).reset(wires)
        return c
    return {"native":native,"sdk_scalar":scalar,"sdk_batch":grouped}


def native_circuit(c):
    return c if isinstance(c,QuantumCircuit) else c.to_qiskit()


def verify_build(functions):
    reference=native_circuit(functions["native"]())
    for name,fn in functions.items():
        observed=native_circuit(fn())
        if reference!=observed:
            raise AssertionError(f"native instruction mismatch: {name}")
    return {"instructions":len(reference.data),"oracle":"exact native circuit equality"}


def state_functions(n,count):
    builders=make_build(n,count)
    native=builders["native"]()
    sdk=builders["gates"]()
    rng=np.random.default_rng(2718+n)
    data=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    data/=np.linalg.norm(data)
    # Same complex input and independent output copies; Ketary also validates snapshot.
    return {"native":lambda:Statevector(data).evolve(native).data.copy(),
            "sdk":lambda:sdk.run(initial_state=data).math.statevector()}


def math_functions(n,count):
    rng=random.Random(917+n)
    unique=["".join(rng.choices("IXYZ",k=n)) for _ in range(max(1,count//4))]
    labels=(unique*4)[:count]
    native=Statevector.from_instruction(q.ghz(n).to_qiskit())
    sdk=q.ghz(n).run()
    def qiskit_cached():
        cache={label:float(native.expectation_value(Pauli(label)).real) for label in sorted(set(labels))}
        return tuple(cache[label] for label in labels)
    return {"native":lambda:tuple(float(native.expectation_value(Pauli(x)).real) for x in labels),
            "native_cached":qiskit_cached,
            "sdk_scalar":lambda:tuple(sdk.math.expectation(x) for x in labels),
            "sdk_grouped":lambda:sdk.math.expectations(labels)}


def verify_numeric(functions):
    ref=functions["native"]()
    err={}
    for name,fn in functions.items():
        observed=fn()
        np.testing.assert_allclose(observed,ref,atol=TOL,rtol=0)
        err[name]=float(np.max(np.abs(np.asarray(observed)-np.asarray(ref))))
    return {"oracle":"native complex state or real mathematical result","max_error":err}


def rss_worker(case,variant):
    if case=="build100k":
        functions=make_build(8,100000)
    else:
        functions=state_functions(20,16)
    gc.collect()
    before=memory_kib()
    result=functions[variant]()
    after=memory_kib()
    if case=="build100k":
        assert len(native_circuit(result).data)==100000
    else:
        assert np.isclose(np.linalg.norm(result),1)
    return {"case":case,"variant":variant,"before":before,"after":after}


def writing():
    result=writing_study()
    # Author-matched source pairs. Do not aggregate unrelated semantics.
    pairs=[
        ("dynamic_measure_reset",
         "c=QuantumCircuit(4,4)\nc.measure(range(4),range(4))\nc.reset(range(4))",
         "c=q.Circuit.classical(4,4)\nc.measure(c.wires,c.wires).reset(c.wires)"),
        ("permuted_readout",
         "c=QuantumCircuit(4,4)\nc.measure([3,0,2],[0,2,1])",
         "c=q.Circuit.classical(4,4).measure([3,0,2],[0,2,1])"),
        ("star_entanglement",
         "c=QuantumCircuit(4)\nc.h(0)\nc.cx(0,[1,2,3])",
         "c=q.Circuit(4).h(0).apply_each(q.Circuit(2).cx(0,1),placements=q.star(range(4)))"),
    ]
    extra=[]
    for name,a,b in pairs:
        env={"QuantumCircuit":QuantumCircuit,"q":q}
        exec(compile(a,name+":native","exec"),env)
        expected=env.pop("c")
        exec(compile(b,name+":sdk","exec"),env)
        observed=env["c"].to_qiskit()
        assert expected==observed
        extra.append({"case":name,"native":metrics(a),"ketary":metrics(b),
                      "oracle":"exact native circuit equality","matched":True,
                      "native_source":a,"ketary_source":b})
    return {"existing":result,"extra":extra}


def main(reps,seed,smoke):
    data={"commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
          "python":sys.version,"qiskit":qiskit.__version__,"numpy":np.__version__,
          "platform":platform.platform(),"cpu":platform.processor(),
          "cpu_count":os.cpu_count(),"seed":seed,"repetitions":reps,"smoke":smoke,
          "affinity":sorted(os.sched_getaffinity(0)) if hasattr(os,"sched_getaffinity") else None,
          "threads":{key:os.environ.get(key) for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","RAYON_NUM_THREADS")},
          "cases":[],"rss":[],"writing":writing()}
    def add(name,params,functions,numeric=False):
        checked=verify_numeric(functions) if numeric else verify_build(functions)
        row={"case":name,**params,"correctness":checked,**paired(functions,reps,seed+len(data["cases"]))}
        data["cases"].append(row)
        print(json.dumps({"case":name,**params,"medians_ms":{k:v["median_ms"] for k,v in row["samples"].items()},"correctness":checked}),file=sys.stderr,flush=True)
    for count in ([100] if smoke else [1000,10000,100000]):
        add("mixed_build",{"n":8,"gates":count},make_build(8,count))
    for count in ([10] if smoke else [100,1000,10000]):
        add("repeat_layer",{"n":8,"layers":count},repeat_build(count))
    for count in ([10] if smoke else [100,1000,5000]):
        add("single_wire_batch",{"n":8,"layers":count},batch_build(count))
    for n,layers in ([(4,3)] if smoke else [(8,100),(16,100),(32,500)]):
        add("pair_placement",{"n":n,"layers":layers},pair_build(n,layers))
    for layers in ([2] if smoke else [8,32,64]):
        add("dynamic_batch",{"n":8,"layers":layers},dynamic_build(layers))
    for n,count in ([(4,8)] if smoke else [(8,128),(12,128),(16,64),(18,32),(20,16)]):
        add("statevector",{"n":n,"gates":count},state_functions(n,count),True)
    for n,count in ([(4,4)] if smoke else [(8,4),(12,16),(16,32),(20,16)]):
        add("grouped_math",{"n":n,"queries":count},math_functions(n,count),True)
    if not smoke:
        for case,variants in (("build100k",("native","gates","fluent")),("state20",("native","sdk"))):
            for variant in variants:
                cmd=[sys.executable,__file__,"--rss-case",case,"--rss-variant",variant]
                data["rss"].append(json.loads(subprocess.check_output(cmd,text=True)))
    return data


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repetitions",type=int,default=30)
    p.add_argument("--seed",type=int,default=1)
    p.add_argument("--smoke",action="store_true")
    p.add_argument("--rss-case",choices=["build100k","state20"])
    p.add_argument("--rss-variant")
    a=p.parse_args()
    if a.rss_case:
        result=rss_worker(a.rss_case,a.rss_variant)
    else:
        if not 3<=a.repetitions<=100 or (a.repetitions<20 and not a.smoke):
            p.error("20..100 repetitions (smoke: 3..100)")
        result=main(a.repetitions,a.seed,a.smoke)
    print(json.dumps(result,indent=2,allow_nan=False))
