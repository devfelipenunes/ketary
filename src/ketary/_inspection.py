"""Bounded structured read models over authoritative Qiskit / Result."""
from itertools import islice
from collections.abc import Mapping
from ._validation import _int, _tol, _real, ResourceLimit

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
        operations.append({"index":i+1,"gate":item.name,
            "wires":[raw.find_bit(w).index for w in item.qubits],
            "params":[float(p) for p in item.params]})
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
    from ._contracts import _evaluate,_expectation_predicates
    p=[]
    if probabilities is not None:
        if not isinstance(probabilities,Mapping):
            raise TypeError("expected probability mapping")
        # Preflight all predicates before evaluating even the first check.
        # Retain the existing insertion order and legacy report schema.
        for label in _labels(probabilities):
            if len(label)!=result.num_qubits or set(label)-set("01"):
                raise ValueError("invalid bit string")
            value=_real(probabilities[label])
            if not 0<=value<=1:
                raise ValueError("invalid probability")
            p.append((label,value))
    e=_expectation_predicates(expectations,result.num_qubits,ordered=True)
    if len(p)+len(e)+int(normalized)>32:
        raise ResourceLimit("aggregate check cap exceeded")
    report=_evaluate(result,p,e,normalized,t).to_dict()
    # Preserve the existing public dictionary scope and empty-check behavior.
    report["scope"]="explicit ideal snapshot checks only"
    return report
