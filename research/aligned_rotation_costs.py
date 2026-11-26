"""RF03/RF25: scale aligned rotations without changing output semantics.

Compare fluent per-gate loops, public aligned/scalar batches and native
Qiskit. Measure construction separately from Python tracemalloc peak.
Tracemalloc is NOT process RSS, native allocation or hardware evidence.
"""
import argparse,json,random,statistics,time,tracemalloc,platform
from pathlib import Path
from importlib.metadata import version
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

def native(c):return c.to_qiskit() if isinstance(c,q.Circuit) else c
def case(gate,count,mode,seed,reps):
    rng=np.random.default_rng(seed)
    pairs=[(0,1),(2,0),(1,2)]*(count//3)+[(0,1),(2,0),(1,2)][:count%3]
    angles=[.37]*count if mode=="scalar" else rng.uniform(-1,1,count).tolist()
    def sdk_loop():
        c=q.Circuit(3);fn=getattr(c,gate)
        for angle,(a,b) in zip(angles,pairs,strict=True):fn(angle,a,b)
        return c
    def sdk_batch():
        c=q.Circuit(3);getattr(c,gate)(angles[0] if mode=="scalar" else angles,pairs=pairs);return c
    def native_loop():
        c=QuantumCircuit(3);fn=getattr(c,gate)
        for angle,(a,b) in zip(angles,pairs,strict=True):fn(angle,a,b)
        return c
    def native_batch():
        c=QuantumCircuit(3);getattr(c,gate)(angles[0],[a for a,b in pairs],[b for a,b in pairs]);return c
    builds={"sdk_loop":sdk_loop,"sdk_batch":sdk_batch,"native_loop":native_loop}
    if mode=="scalar":builds["native_broadcast"]=native_batch
    ref=native_loop()
    for k,build in builds.items():
        raw=native(build())
        if raw!=ref:raise AssertionError(f"{gate}/{count}/{mode}/{k}: ordered native sequence mismatch")
        if count<=100:
            np.testing.assert_allclose(Operator(raw).data,Operator(ref).data,atol=1e-9,rtol=0)
    samples={k:[] for k in builds};order_rng=random.Random(seed)
    for _ in range(reps):
        order=list(builds);order_rng.shuffle(order)
        for k in order:
            t=time.perf_counter_ns();c=builds[k]();samples[k].append((time.perf_counter_ns()-t)/1e6)
    result={}
    for k,build in builds.items():
        tracemalloc.start()
        try:
            c=build();_,peak=tracemalloc.get_traced_memory()
        finally:tracemalloc.stop()
        result[k]={"raw_ms":samples[k],"p50_ms":statistics.median(samples[k]),"p95_ms":float(np.quantile(samples[k],.95)),"python_peak_bytes":peak}
    return {"gate":gate,"pairs":count,"mode":mode,"variants":result,"verification":"ordered native sequence; full operator <=100 pairs"}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--seed",type=int,default=1101);p.add_argument("--reps",type=int,default=7);a=p.parse_args()
    if not 3<=a.reps<=30:p.error("3..30 repetitions")
    rows=[]
    for gate in ("cp","rzz"):
        for count in (1,10,100,1000,10000):
            for mode in ("scalar","aligned"):
                row=case(gate,count,mode,a.seed,a.reps);rows.append(row);print(json.dumps(row),flush=True)
    a.output.write_text(json.dumps({"scope":"shared CI construction diagnostics; tracemalloc Python only","python":platform.python_version(),"qiskit":version("qiskit"),"seed":a.seed,"rows":rows},indent=2,allow_nan=False))
if __name__=="__main__":main()
