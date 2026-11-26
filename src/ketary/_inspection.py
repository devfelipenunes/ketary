"""Bounded structured read models over authoritative Qiskit / Result."""
from itertools import islice
from collections.abc import Mapping
from ._validation import _int, _tol, ResourceLimit

def inspect_circuit(circuit, *, start=0, limit=32):
    start=_int(start); limit=_int(limit,1)
    if limit>256: raise ResourceLimit("inspection page exceeds 256 operations")
    raw=circuit._qc
    total=len(raw.data)
    if start>total: raise ValueError("inspection offset exceeds gate count")
    stop=min(start+limit,total)
    operations=[]
    # Index only the requested window; no full circuit copy, scan or run.
    for i in range(start,stop):
        item=raw.data[i]
        operations.append({"index":i+1,"gate":item.operation.name,
            "wires":[raw.find_bit(w).index for w in item.qubits],
            "params":[float(p) for p in item.operation.params]})
    return {"schema_version":1,"num_qubits":raw.num_qubits,"global_phase":float(raw.global_phase),
            "gate_count":total,"bit_order":"highest-wire-first","operations":operations,
            "start":start,"next_start":stop if stop<total else None,"omitted":total-len(operations)}

def _labels(values):
    if isinstance(values,str): raise ValueError("expected iterable of labels, not string")
    labels=list(islice(iter(values),33))
    if len(labels)>32: raise ResourceLimit("evidence label cap exceeded")
    if any(type(v) is not str for v in labels) or len(set(labels))!=len(labels):
        raise ValueError("labels must be distinct strings")
    return labels

def result_evidence(result, *, bits, paulis):
    bits=_labels(bits); paulis=_labels(paulis)
    # Fixed output bounds; no enumeration of all basis labels.
    rows={}
    for label in bits:
        a=result.math.amplitude(label)
        rows[label]={"amplitude":[a.real,a.imag],"probability":result.math.probability(label)}
    return {"schema_version":1,"scope":"ideal pure-state snapshot","bit_order":"highest-wire-first",
            "num_qubits":result.num_qubits,"basis":rows,
            "expectations":{p:result.math.expectation(p) for p in paulis},
            "norm":result.math.norm()}

def verify_result(result, *, probabilities, expectations, normalized, atol):
    if type(normalized) is not bool: raise ValueError("normalized must be bool")
    t=_tol(atol)
    requested=[]
    for name,values in (("probability",probabilities),("expectation",expectations)):
        if values is None: continue
        if not isinstance(values,Mapping): raise TypeError("expected mapping of labels to targets")
        labels=_labels(values)
        for label in labels: requested.append((name,label,values[label]))
    if len(requested)+int(normalized)>32: raise ResourceLimit("aggregate check cap exceeded")
    records={}
    if normalized: records["normalized"]=result.test.normalized(atol=t).to_dict()
    for kind,label,expected in requested:
        check=getattr(result.test,kind)(label,expected,atol=t)
        records[f"{kind}:{label}"]=check.to_dict()
    statuses=[v["status"] for v in records.values()]
    status="FAIL" if "FAIL" in statuses else "UNSUPPORTED" if not statuses or "UNSUPPORTED" in statuses else "PASS"
    return {"schema_version":1,"scope":"explicit ideal snapshot checks only","status":status,"checks":records}
