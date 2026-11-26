"""I03/I04/I06 research helpers over the existing Circuit, not a new API."""
from hashlib import sha256
import json
import ketary as q
import numpy as np
from qiskit.quantum_info import Operator
from contracts import Report


def _bounded(c):
    if not isinstance(c,q.Circuit):
        raise TypeError("expected Circuit")
    head=c.inspect(limit=1)
    if head["num_qubits"]>8 or head["gate_count"]>256:
        raise q.ResourceLimit("research scope: <=8 qubits, <=256 operations")
    return c.inspect(limit=256)


def semantic_inspect(c,*,source=None):
    """Wire-order dependency graph, not proof of physical causation."""
    page=_bounded(c)
    last={}
    dependencies=[]
    wires={str(i):[] for i in range(c.num_qubits)}
    for op in page["operations"]:
        idx=op["index"]
        predecessors=sorted({last[w] for w in op["wires"] if w in last})
        dependencies.append({"index":idx,"predecessors":predecessors})
        for w in op["wires"]:
            last[w]=idx
            wires[str(w)].append(idx)
    provenance={"status":"UNAVAILABLE","reason":"no literal source supplied"}
    if source is not None:
        from source_reader import read_source
        parsed=read_source(source)
        if (parsed["status"]=="PASS" and parsed["num_qubits"]==c.num_qubits
            and page["global_phase"]==0
            and [_signature(x) for x in parsed["operations"]]==[_signature(x) for x in page["operations"]]):
            provenance={"status":"MATCH","scope":"literal source matches runtime operations; not proof of execution origin",
                        "locations":[{k:op[k] for k in ("index","line","column","end_column")} for op in parsed["operations"]]}
        else:
            provenance={"status":"UNSUPPORTED","reason":"literal source unavailable or does not match runtime"}
    return {"schema_version":1,"scope":"structural wire ordering only; no entanglement or causal proof",
            "circuit":page,"wire_operations":wires,"dependencies":dependencies,"provenance":provenance}


def diagnose(observed,reference,*,paulis=()):
    """Explicit simulation. Checkpoints are not inferred root causes."""
    a,b=_bounded(observed),_bounded(reference)
    if a["num_qubits"]!=b["num_qubits"]:
        return Report.from_data({"schema_version":1,"status":"UNSUPPORTED","scope":"diagnosis",
                                 "reason":"width mismatch"})
    actual,expected=observed.run(),reference.run()
    distribution=actual.test.distribution(expected).to_dict()
    state=actual.test.state(expected).to_dict()
    operator=observed.test.equivalent(reference).to_dict()
    trace=observed.debug.compare(reference).to_dict()
    act=actual.evidence(paulis=paulis)["expectations"]
    # A generator may have been consumed by the first evidence call.
    exp=expected.evidence(paulis=list(act))["expectations"]
    checks={"distribution":distribution,"state":state,"operator":operator}
    for p in act:
        checks["expectation:"+p]=actual.test.expectation(p,exp[p]).to_dict()
    status=operator["status"]
    return Report.from_data({"schema_version":1,"scope":"ideal zero-input states and strict full operator; aligned trace is not root cause",
                             "status":status,"checks":checks,"trace":trace,
                             "hypothesis":"state differs despite matching measurement distribution"
                             if distribution["status"]=="PASS" and state["status"]=="FAIL" else None})


def _digest(c):
    return sha256(c.to_json().encode()).hexdigest()


def _signature(op):
    return (op["gate"],tuple(op["wires"]),tuple(op["params"]))


def suggest_repair(observed,reference,*,max_candidates=32):
    """Reference-guided single edit, with strict independent operator check.

    Never applies a patch. Only consider the first differing operation or
    one extra/missing operation; no search over arbitrary programs.
    """
    if type(max_candidates) is not int or not 1<=max_candidates<=32:
        raise ValueError("max_candidates must be 1..32")
    a,b=_bounded(observed),_bounded(reference)
    base={"schema_version":1,"scope":"single reference-guided edit; strict full operator",
          "observed_sha256":_digest(observed),"candidates":[]}
    if a["num_qubits"]!=b["num_qubits"] or abs(a["global_phase"]-b["global_phase"])>1e-9:
        return dict(base,status="UNSUPPORTED",reason="width or explicit phase mismatch")
    ops=a["operations"]; target=b["operations"]
    if abs(len(ops)-len(target))>1:
        return dict(base,status="UNSUPPORTED",reason="more than one insertion/deletion required")
    expected=Operator(reference.to_qiskit()).data
    if np.allclose(Operator(observed.to_qiskit()).data,expected,atol=1e-9,rtol=0):
        return dict(base,status="ALREADY_EQUIVALENT",reason="no edit required")
    # Single replacement at a differing index or candidate insert/delete positions.
    if len(ops)==len(target):
        edits=[("replace",i,target[i]) for i in range(len(ops)) if _signature(ops[i])!=_signature(target[i])]
    elif len(ops)>len(target):
        edits=[("delete",i,None) for i in range(len(ops))]
    else:
        edits=[("insert",i,target[i]) for i in range(len(target))]
    if len(edits)>max_candidates:
        return dict(base,status="UNSUPPORTED",reason="candidate budget exceeded")
    native=observed.to_qiskit()
    ref=reference.to_qiskit()
    for kind,i,new in edits:
        rebuilt=native.copy_empty_like()
        rebuilt.global_phase=native.global_phase
        instructions=list(native.data)
        if kind=="delete":
            instructions.pop(i)
        else:
            item=ref.data[i]
            # Build using ordered reference wires, then map to observed register.
            from qiskit.circuit import CircuitInstruction
            mapped=CircuitInstruction(item.operation,tuple(native.qubits[ref.find_bit(w).index] for w in item.qubits),())
            if kind=="replace":
                instructions[i]=mapped
            else:
                instructions.insert(i,mapped)
        for item in instructions:
            rebuilt.append(item.operation,[native.find_bit(w).index for w in item.qubits],copy=True)
        candidate=q.from_qiskit(rebuilt)
        if np.allclose(Operator(candidate.to_qiskit()).data,expected,atol=1e-9,rtol=0):
            base["candidates"].append({"edit":kind,"index":i+1,"before":ops[i] if kind!="insert" else None,
                                       "after":new,"verified":"strict full operator",
                                       "replay":candidate.to_json()})
    count=len(base["candidates"])
    return dict(base,status="VERIFIED" if count==1 else "AMBIGUOUS" if count>1 else "NO_REPAIR",
                reason="proposals only; caller must review and apply explicitly")
