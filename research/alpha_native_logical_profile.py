"""Matched installed inspection, logical report and replay encoding."""
import json
import random
import time
from dataclasses import asdict
from importlib.metadata import version
import platform
import ketary as q
from research.alpha_native_cost_audit import build
from research.circuit_rewrite_ladder import stats
from ketary._adapter import _validate
from ketary._resources import ResourceReport

def old_inspect(c,start,limit):
    raw=c._qc;total=len(raw.data);stop=min(start+limit,total)
    operations=[]
    for i in range(start,stop):
        item=raw.data[i]
        operations.append({"index":i+1,"gate":item.operation.name,
            "wires":[raw.find_bit(w).index for w in item.qubits],
            "params":[float(p) for p in item.operation.params]})
    return {"schema_version":1,"num_qubits":raw.num_qubits,"global_phase":float(raw.global_phase),
            "gate_count":total,"bit_order":"highest-wire-first","operations":operations,
            "start":start,"next_start":stop if stop<total else None,"omitted":total-len(operations)}

def old_resources(c):
    native=c._qc
    by_gate=tuple(sorted((name,int(count)) for name,count in native.count_ops().items()))
    arities=[item.operation.num_qubits for item in native.data]
    return ResourceReport(native.num_qubits,len(arities),native.depth(),
                          sum(a==2 for a in arities),sum(a>=3 for a in arities),by_gate)

def old_replay(c):
    raw=c._qc;_validate(raw)
    operations=[]
    for item in raw.data:
        op=item.operation
        operations.append({"gate":op.name,"wires":[raw.find_bit(w).index for w in item.qubits],
                           "params":[float(p) for p in op.params]})
    data={"schema_version":1,"num_qubits":raw.num_qubits,"global_phase":float(raw.global_phase),
          "producer":{"ketary":version("ketary"),"qiskit":version("qiskit"),"python":platform.python_version()},
          "operations":operations}
    payload=json.dumps(data,sort_keys=True,separators=(",",":"),allow_nan=False)
    assert len(payload.encode("utf-8"))<=1024*1024
    return payload

def run(seed,reps=9):
    rng=random.Random(seed);rows=[]
    for n,count in ((4,10),(8,100),(20,1000)):
        c=q.from_qiskit(build(n,count,rng));before=c.to_qiskit()
        cases={"inspect":(lambda:old_inspect(c,0,32),lambda:c.inspect(start=0,limit=32)),
               "resources":(lambda:old_resources(c),lambda:c.resources.summary()),
               "replay":(lambda:old_replay(c),lambda:c.to_json())}
        for name,(old,new) in cases.items():
            expected=old();paths={"baseline":old,"candidate":new};samples={k:[] for k in paths}
            for _ in range(reps):
                for k in rng.sample(list(paths),len(paths)):
                    t=time.perf_counter_ns();value=paths[k]();dt=(time.perf_counter_ns()-t)/1e6
                    assert value==expected
                    samples[k].append(dt)
            rows.append(dict(n=n,gates=count,seed=seed,operation=name,paths={k:stats(v) for k,v in samples.items()}))
        assert c.to_qiskit()==before
    return rows

if __name__=="__main__":
    print(json.dumps({"scope":"matched complete report outputs on admitted fixtures; candidate additionally includes public bounds",
      "rows":[r for seed in (1101,2202,3303) for r in run(seed)]},indent=2,allow_nan=False))
