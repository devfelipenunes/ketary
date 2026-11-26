"""Restricted, versioned logical-circuit replay; no executable serialization."""
from __future__ import annotations

import json
import platform
from importlib.metadata import version
from ._adapter import _sdk, _validate
from ._validation import _angle, ResourceLimit

_SCHEMA=1
_MAX_BYTES=1024*1024
_MAX_QUBITS=22
_MAX_GATES=10000
from ._gate_specs import SPECS,MCX_MIN_WIRES,MCX_MAX_WIRES
_ARITY={name:spec[1] for name,spec in SPECS.items()}

def _keys(value,expected):
    if type(value) is not dict or set(value)!=set(expected):
        raise ValueError("unexpected replay object fields")

def _unique_pairs(pairs):
    out={}
    for key,value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key")
        out[key]=value
    return out

def _reject_constant(value):
    raise ValueError("nonfinite JSON constant")

def _width_and_count(n,count):
    if type(n) is not int or n<1:
        raise ValueError("invalid qubit count")
    if n>_MAX_QUBITS or count>_MAX_GATES:
        raise ResourceLimit("replay qubit or gate limit exceeded")

def _encode(circuit):
    qc=circuit._qc
    _width_and_count(qc.num_qubits,len(qc.data))
    _validate(qc)
    operations=[]
    for item in qc.data:
        op=item.operation
        if op.name not in _ARITY and op.name!='mcx':
            raise ValueError("unsupported replay gate")
        operations.append({
            "gate":op.name,
            "wires":[qc.find_bit(wire).index for wire in item.qubits],
            "params":[float(p) for p in op.params],
        })
    data={
        "schema_version":_SCHEMA,
        "num_qubits":qc.num_qubits,
        "global_phase":float(qc.global_phase),
        "producer":{"ketary":version("ketary"),"qiskit":version("qiskit"),"python":platform.python_version()},
        "operations":operations,
    }
    payload=json.dumps(data,sort_keys=True,separators=(",",":"),allow_nan=False)
    if len(payload.encode("utf-8"))>_MAX_BYTES:
        raise ResourceLimit("replay JSON byte limit exceeded")
    return payload

def _decode(payload):
    if type(payload) is not str:
        raise TypeError("expected JSON text")
    if len(payload)>_MAX_BYTES:
        raise ResourceLimit("replay JSON byte limit exceeded")
    try:
        if len(payload.encode("utf-8"))>_MAX_BYTES:
            raise ResourceLimit("replay JSON byte limit exceeded")
        data=json.loads(payload,object_pairs_hook=_unique_pairs,parse_constant=_reject_constant)
    except (UnicodeError,RecursionError) as exc:
        raise ValueError("invalid replay JSON") from exc
    _keys(data,("schema_version","num_qubits","global_phase","producer","operations"))
    if type(data["schema_version"]) is not int or data["schema_version"]!=_SCHEMA:
        raise ValueError("unsupported replay schema version")
    producer=data["producer"]
    _keys(producer,("ketary","qiskit","python"))
    if any(type(v) is not str or not v or len(v)>100 for v in producer.values()):
        raise ValueError("invalid replay producer metadata")
    n=data["num_qubits"]
    ops=data["operations"]
    if type(ops) is not list:
        raise ValueError("operations must be a list")
    _width_and_count(n,len(ops))
    phase=_angle(data["global_phase"])
    # Validate the complete artifact before allocating a circuit.
    validated=[]
    for item in ops:
        _keys(item,("gate","wires","params"))
        name,wires,params=item["gate"],item["wires"],item["params"]
        if type(name) is not str or (name not in _ARITY and name!='mcx'):
            raise ValueError("unsupported replay gate")
        if (type(wires) is not list or (not MCX_MIN_WIRES<=len(wires)<=MCX_MAX_WIRES if name=="mcx" else len(wires)!=_ARITY[name])
            or any(type(w) is not int or w<0 or w>=n for w in wires)
            or len(set(wires))!=len(wires)):
            raise ValueError("invalid replay wires")
        if type(params) is not list or len(params)!=(0 if name=='mcx' else SPECS[name][2]):
            raise ValueError("invalid replay parameter count")
        validated.append((name,tuple(_angle(p) for p in params),tuple(wires)))
    QC,_=_sdk()
    qc=QC(n,global_phase=phase)
    for name,params,wires in validated:
        # Only statically allowlisted standard gate names reach this call.
        if name=="mcx":
            from qiskit.circuit.library import MCXGate
            qc.append(MCXGate(len(wires)-1),list(wires))
        else:
            getattr(qc,name)(*params,*wires)
    return qc
