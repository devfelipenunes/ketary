"""R07 paired, deterministic semantic workflows (not LLM trials).

All variants receive the same trusted circuit and task. No dynamic user
source execution. Canonical outputs describe identical requested facts;
raw return values and extra information are measured separately.
"""
import inspect
import json
from collections import Counter
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli
from ketary_eval import lexical

VARIANTS=("qiskit","ketary","candidate")
ATOL=1e-9


def cases():
    rows=[]
    for i in range(6):
        n=3+i%2
        gates=[("h",0),("cx",0,1),("rz",.3,2),("swap",0,2)]
        gates=(gates*(1+i*8))+[("x",1)]
        start=[0,1,31,32,len(gates)-1,len(gates)][i]
        rows.append(dict(id=f"I{i+1:02}",kind="inspect",n=n,gates=gates,
                         start=start,limit=3+i))
    for i in range(6):
        n=2+i%3
        gates=[("h",0),("cx",0,1)]
        if i%2: gates.append(("z",0))
        if i>=4: gates.append(("s",1))
        bits=["0"*n,format(3,f"0{n}b"),format(1,f"0{n}b")]
        paulis=["I"*(n-2)+p for p in ("XX","ZZ","YX")]
        rows.append(dict(id=f"E{i+1:02}",kind="evidence",n=n,gates=gates,
                         bits=bits,paulis=paulis))
    for i in range(6):
        n=2+i%3
        gates=[("h",0),("cx",0,1)]
        if i%2: gates.append(("z",0))
        rows.append(dict(id=f"V{i+1:02}",kind="verify",n=n,gates=gates,
            probabilities={"0"*n:.5,format(3,f"0{n}b"):.5 if i<4 else .25},
            expectations={"I"*(n-2)+"XX":1,"I"*(n-2)+"ZZ":1},
            normalized=True))
    for i in range(6):
        n=2+i%3
        ref=[("h",0),("cx",0,1)]
        obs=ref.copy()
        if i==0: obs[1]=("cx",1,0)
        elif i==1: ref.append(("x",0)); obs.append(("z",0))
        elif i==2: ref.append(("z",1)); obs.append(("z",1))
        elif i==3: obs.append(("x",0))
        elif i==4: ref.append(("x",0)); obs.append(("x",1))
        else: ref.append(("h",0)); obs.append(("z",0))
        rows.append(dict(id=f"D{i+1:02}",kind="debug",n=n,gates=obs,reference=ref))
    return rows


CASES=cases()


def build(n,gates,variant):
    c=QuantumCircuit(n) if variant=="qiskit" else q.Circuit(n)
    for name,*args in gates:
        target=c.gates if variant=="ketary" else c
        getattr(target,name)(*args)
    return c


def native_page(c,task):
    start,limit=task["start"],task["limit"]
    stop=min(start+limit,len(c.data))
    operations=[]
    for i in range(start,stop):
        item=c.data[i]
        operations.append({"index":i+1,"gate":item.operation.name,
            "wires":[c.find_bit(w).index for w in item.qubits],
            "params":[float(p) for p in item.operation.params]})
    return {"gate_count":len(c.data),"operations":operations,
            "next_start":stop if stop<len(c.data) else None}


def qiskit_inspect(c,t):
    return native_page(c,t)


def ketary_inspect(c,t):
    return native_page(c.to_qiskit(),t)


def candidate_inspect(c,t):
    return c.inspect(start=t["start"],limit=t["limit"])


def qiskit_evidence(c,t):
    r=Statevector.from_instruction(c)
    basis={}
    for b in t["bits"]:
        a=r.data[int(b,2)]
        basis[b]={"amplitude":[float(a.real),float(a.imag)],"probability":float(abs(a)**2)}
    return {"basis":basis,"expectations":{p:float(r.expectation_value(Pauli(p)).real)
            for p in t["paulis"]},"norm":float(np.linalg.norm(r.data))}


def ketary_evidence(c,t):
    r=c.run()
    basis={}
    for b in t["bits"]:
        a=r.math.amplitude(b)
        basis[b]={"amplitude":[a.real,a.imag],"probability":r.math.probability(b)}
    return {"basis":basis,"expectations":{p:r.math.expectation(p) for p in t["paulis"]},
            "norm":r.math.norm()}


def candidate_evidence(c,t):
    return c.run().evidence(bits=t["bits"],paulis=t["paulis"])


def qiskit_verify(c,t):
    r=Statevector.from_instruction(c)
    checks={}
    if t["normalized"]:
        checks["normalized"]={"status":"PASS" if abs(np.linalg.norm(r.data)-1)<=ATOL else "FAIL"}
    for b,expected in t["probabilities"].items():
        actual=abs(r.data[int(b,2)])**2
        checks[f"probability:{b}"]={"status":"PASS" if abs(actual-expected)<=ATOL else "FAIL"}
    for p,expected in t["expectations"].items():
        actual=r.expectation_value(Pauli(p)).real
        checks[f"expectation:{p}"]={"status":"PASS" if abs(actual-expected)<=ATOL else "FAIL"}
    return {"status":"PASS" if all(x["status"]=="PASS" for x in checks.values()) else "FAIL",
            "checks":checks}


def ketary_verify(c,t):
    r=c.run()
    checks={}
    if t["normalized"]:
        checks["normalized"]=r.test.normalized().to_dict()
    for b,expected in t["probabilities"].items():
        checks[f"probability:{b}"]=r.test.probability(b,expected).to_dict()
    for p,expected in t["expectations"].items():
        checks[f"expectation:{p}"]=r.test.expectation(p,expected).to_dict()
    return {"status":"PASS" if all(x["status"]=="PASS" for x in checks.values()) else "FAIL",
            "checks":checks}


def candidate_verify(c,t):
    return c.run().verify(probabilities=t["probabilities"],expectations=t["expectations"],
                          normalized=t["normalized"])


def qiskit_debug(c,t):
    ref=build(t["n"],t["reference"],"qiskit")
    if len(c.data)!=len(ref.data):
        return {"status":"UNSUPPORTED","step_index":None,"actual_operation":None}
    a=b=Statevector.from_label("0"*t["n"])
    for i,(x,y) in enumerate(zip(c.data,ref.data,strict=True),1):
        a=a.evolve(x.operation,qargs=[c.find_bit(w).index for w in x.qubits])
        b=b.evolve(y.operation,qargs=[ref.find_bit(w).index for w in y.qubits])
        if not a.equiv(b,atol=ATOL,rtol=0):
            return {"status":"FAIL","step_index":i,"actual_operation":x.operation.name}
    return {"status":"PASS","step_index":None,"actual_operation":None}


def ketary_debug(c,t):
    ref=build(t["n"],t["reference"],"ketary")
    report=c.debug.compare(ref)
    return {"status":report.check.status,"step_index":report.step_index,
            "actual_operation":report.actual_operation}


def candidate_debug(c,t):
    ref=build(t["n"],t["reference"],"candidate")
    return c.debug.compare(ref).to_dict()


METHODS={
    "inspect":(qiskit_inspect,ketary_inspect,candidate_inspect),
    "evidence":(qiskit_evidence,ketary_evidence,candidate_evidence),
    "verify":(qiskit_verify,ketary_verify,candidate_verify),
    "debug":(qiskit_debug,ketary_debug,candidate_debug),
}


def canonical(kind,raw):
    if kind=="inspect":
        return {k:raw[k] for k in ("gate_count","operations","next_start")}
    if kind=="evidence":
        return {k:raw[k] for k in ("basis","expectations","norm")}
    if kind=="verify":
        return {"status":raw["status"],"checks":{k:v["status"] for k,v in raw["checks"].items()}}
    return {"status":raw["check"]["status"] if "check" in raw else raw["status"],
            "step_index":raw["step_index"],"actual_operation":raw["actual_operation"]}


def equal(a,b):
    if isinstance(a,dict) and isinstance(b,dict):
        return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):
        return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if type(a) in (int,float) and type(b) in (int,float):
        return bool(np.isclose(a,b,atol=ATOL,rtol=0))
    return type(a)==type(b) and a==b


def execute(task,variant):
    method=METHODS[task["kind"]][VARIANTS.index(variant)]
    circuit=build(task["n"],task["gates"],variant)
    raw=method(circuit,task)
    return raw,canonical(task["kind"],raw)


def bytes_json(obj):
    return len(json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8"))


def benchmark():
    rows=[]
    for task in CASES:
        _,expected=execute(task,"qiskit")
        for variant in VARIANTS:
            raw,answer=execute(task,variant)
            assert equal(answer,expected),(task["id"],variant,answer,expected)
            method=METHODS[task["kind"]][VARIANTS.index(variant)]
            # Count complete authored function bodies, plus shared helper where
            # actually needed; do not count construction of the identical input.
            code=inspect.getsource(method)
            if task["kind"]=="inspect" and variant!="candidate":
                code+=inspect.getsource(native_page)
            rows.append(dict(id=task["id"],kind=task["kind"],variant=variant,
                semantic_match=True,workflow_lexical_tokens=lexical(code),
                raw_json_bytes=bytes_json(raw),canonical_json_bytes=bytes_json(answer)))
    totals={}
    for kind in METHODS:
        totals[kind]={}
        for variant in VARIANTS:
            group=[r for r in rows if r["kind"]==kind and r["variant"]==variant]
            totals[kind][variant]={key:sum(r[key] for r in group) for key in
                ("workflow_lexical_tokens","raw_json_bytes","canonical_json_bytes")}
    return {"cases":len(CASES),"paired_runs":len(rows),"categories":dict(Counter(t["kind"] for t in CASES)),
            "totals":totals,"rows":rows,
            "limitations":"authored deterministic workflows; lexical tokens are not LLM tokens; raw reports differ in detail; no speed or human/model performance claim"}


if __name__=="__main__":
    print(json.dumps(benchmark(),indent=2,allow_nan=False))
