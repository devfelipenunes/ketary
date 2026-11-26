"""Bounded verification, explicit counterexamples and reproducible artifacts.

Selected inputs can disprove an equivalence claim but cannot prove it.
No implicit execution, arbitrary deserialization or second simulator.
"""
import json
import platform
from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import version
from itertools import islice
import numpy as np
from ._validation import _int,_tol,_limit,ResourceLimit
from ._replay import _unique_pairs,_reject_constant,_keys


def _json(data):
    return json.dumps(data,sort_keys=True,separators=(",",":"),allow_nan=False)


def _pair(a,b,max_bytes):
    from ._circuit import Circuit
    if not isinstance(a,Circuit) or not isinstance(b,Circuit):
        raise TypeError("expected Circuit pair")
    a._require_bound()
    b._require_bound()
    if a.num_qubits!=b.num_qubits:
        raise ValueError("circuit width mismatch")
    if a.num_qubits>12 or max(len(a._qc.data),len(b._qc.data))>256:
        raise ResourceLimit("comparison supports <=12 qubits and 256 gates per circuit")
    _limit(a.num_qubits,4,budget=max_bytes)


def _label(label,n):
    if type(label) is not str or len(label)!=n or set(label)-set("01+-rl"):
        raise ValueError("expected full-width product-state label over 01+-rl")
    return label


def _outputs(a,b,label,max_bytes):
    from qiskit.quantum_info import Statevector
    initial=Statevector.from_label(_label(label,a.num_qubits)).data
    return a.run(initial_state=initial,max_bytes=max_bytes),b.run(initial_state=initial,max_bytes=max_bytes)


def _distance(a,b,ignore_global_phase):
    x=a._data
    y=b._data
    if ignore_global_phase:
        overlap=np.vdot(y,x)
        if abs(overlap)>0:
            x=x*(np.conj(overlap)/abs(overlap))
    return float(np.linalg.norm(x-y))


def _snapshot(a,b,label,ignore_global_phase,max_bytes):
    x,y=_outputs(a,b,label,max_bytes)
    return {"input":label,"state_l2":_distance(x,y,ignore_global_phase),
            "distribution_tv":x.test.distribution(y).actual,
            "fidelity":x.math.fidelity(y)}


def _environment():
    return {"ketary":version("ketary"),"qiskit":version("qiskit"),"numpy":version("numpy"),
            "python":platform.python_version()}


def _make_evidence(a,b,label,ignore_global_phase,atol,actual):
    data={"schema_version":1,"kind":"product-state-l2-counterexample",
          "observed":a.to_json(),"reference":b.to_json(),"input":label,
          "ignore_global_phase":ignore_global_phase,"atol":atol,
          "recorded_distance":actual,"producer":_environment()}
    return Evidence.from_json(_json({"data":data,"sha256":sha256(_json(data).encode()).hexdigest()}))


@dataclass(frozen=True,init=False)
class Evidence:
    """Immutable content-addressed counterexample. Hash is not authentication."""
    _payload: str

    def __init__(self):
        raise TypeError('use Evidence.from_json')

    @classmethod
    def from_json(cls,payload):
        if type(payload) is not str:
            raise TypeError("expected JSON text")
        if len(payload)>2*1024*1024:
            raise ResourceLimit("evidence byte limit exceeded")
        try:
            if len(payload.encode("utf-8"))>2*1024*1024:
                raise ResourceLimit("evidence byte limit exceeded")
            envelope=json.loads(payload,object_pairs_hook=_unique_pairs,parse_constant=_reject_constant)
        except (UnicodeError,RecursionError) as exc:
            raise ValueError("invalid evidence JSON") from exc
        _keys(envelope,("data","sha256"))
        d=envelope["data"]
        _keys(d,("schema_version","kind","observed","reference","input","ignore_global_phase","atol","recorded_distance","producer"))
        if type(d["schema_version"]) is not int or d["schema_version"]!=1 or d["kind"]!="product-state-l2-counterexample":
            raise ValueError("unsupported evidence schema")
        if envelope["sha256"]!=sha256(_json(d).encode()).hexdigest():
            raise ValueError("evidence content hash mismatch")
        _keys(d["producer"],("ketary","qiskit","numpy","python"))
        if any(type(v) is not str or not v or len(v)>100 for v in d["producer"].values()):
            raise ValueError("invalid producer")
        if type(d["ignore_global_phase"]) is not bool:
            raise ValueError("invalid phase policy")
        t=_tol(d["atol"])
        if not t<_tol(d["recorded_distance"])<=2+1e-8:
            raise ValueError("artifact must record a failing witness")
        from ._circuit import Circuit
        a,b=Circuit.from_json(d["observed"]),Circuit.from_json(d["reference"])
        _pair(a,b,64*1024**2)
        _label(d["input"],a.num_qubits)
        obj=cls.__new__(cls)
        object.__setattr__(obj,"_payload",_json(envelope))
        return obj

    def to_json(self):
        return self._payload

    def to_dict(self):
        return json.loads(self._payload)

    def reproduce(self,*,max_bytes=64*1024**2):
        from ._circuit import Circuit
        d=self.to_dict()["data"]
        a,b=Circuit.from_json(d["observed"]),Circuit.from_json(d["reference"])
        _pair(a,b,max_bytes)
        record=_snapshot(a,b,d["input"],d["ignore_global_phase"],max_bytes)
        return dict(record,status="FAIL" if record["state_l2"]>d["atol"] else "PASS",
                    reproduced=record["state_l2"]>d["atol"],
                    producer_matches=d["producer"]==_environment(),
                    recorded_distance=d["recorded_distance"],atol=d["atol"],
                    scope="one specified input; not universal equivalence")

    def minimize(self,*,max_attempts=32,max_bytes=64*1024**2):
        """Greedy deletion of observed gates preserving this exact witness."""
        from ._circuit import Circuit
        attempts=_int(max_attempts,1)
        if attempts>128:
            raise ResourceLimit("at most 128 minimization attempts")
        d=self.to_dict()["data"]
        a,b=Circuit.from_json(d["observed"]),Circuit.from_json(d["reference"])
        _pair(a,b,max_bytes)
        if not self.reproduce(max_bytes=max_bytes)["reproduced"]:
            return {"status":"INCONCLUSIVE","reason":"witness no longer reproduces","attempts":0}
        native=a.to_qiskit()
        start=len(native.data)
        i=0
        used=0
        while i<len(native.data) and used<attempts:
            trial=native.copy()
            del trial.data[i]
            candidate=Circuit._from_native(trial,owned=True)
            record=_snapshot(candidate,b,d["input"],d["ignore_global_phase"],max_bytes)
            used+=1
            if record["state_l2"]>d["atol"]:
                native=trial
            else:
                i+=1
        candidate=Circuit._from_native(native,owned=True)
        record=_snapshot(candidate,b,d["input"],d["ignore_global_phase"],max_bytes)
        evidence=_make_evidence(candidate,b,d["input"],d["ignore_global_phase"],d["atol"],record["state_l2"])
        return {"status":"FAIL","scope":"greedy deletion preserving witness; not root cause or global minimum",
                "before_gates":start,"after_gates":len(native.data),"attempts":used,
                "budget_exhausted":used==attempts and i<len(native.data),"evidence":evidence.to_dict()}


def compare(a,b,*,inputs=None,complete=True,ignore_global_phase=False,atol=1e-9,max_bytes=64*1024**2):
    """Escalate selected product inputs to dense operator check, if requested."""
    t=_tol(atol)
    if type(complete) is not bool or type(ignore_global_phase) is not bool:
        raise ValueError("complete and phase policy must be bool")
    _pair(a,b,max_bytes)
    n=a.num_qubits
    if inputs is None:
        inputs=["0"*n,"1"*n,"+"*n,"r"*n]+["0"*(n-i-1)+"1"+"0"*i for i in range(n)]
        inputs=list(dict.fromkeys(inputs))
    if isinstance(inputs,str):
        raise ValueError("expected iterable of input labels")
    labels=list(islice(iter(inputs),33))
    if not 1<=len(labels)<=32:
        raise ValueError("expected 1..32 input labels")
    for label in labels:
        _label(label,n)
    if len(set(labels))!=len(labels):
        raise ValueError("duplicate input labels")
    report={"schema_version":1,"scope":"selected product-state witnesses and optional dense operator norm",
            "phase_policy":"per-input phase ignored; dense overlap alignment" if ignore_global_phase else "strict",
            "atol":t,"status":"INCONCLUSIVE","samples":[],"operator":None,"evidence":None}
    for label in labels:
        record=_snapshot(a,b,label,ignore_global_phase,max_bytes)
        report["samples"].append(record)
        if record["state_l2"]>t:
            report["status"]="FAIL"
            report["evidence"]=_make_evidence(a,b,label,ignore_global_phase,t,record["state_l2"]).to_dict()
            return report
    if complete:
        m=a.test.metrics(b,ignore_global_phase=ignore_global_phase,atol=t,max_bytes=max_bytes)
        report["operator"]=m
        if m["status"]!="UNSUPPORTED":
            report["status"]=m["status"]
    return report


def semantic_diff(a,b,*,atol=1e-9,max_bytes=64*1024**2):
    atol=_tol(atol)
    _pair(a,b,max_bytes)
    left,right=(json.loads(c.to_json()) for c in (a,b))
    for d in (left,right):
        d.pop("producer")
    first=None
    for i in range(max(len(left["operations"]),len(right["operations"]))):
        x=left["operations"][i] if i<len(left["operations"]) else None
        y=right["operations"][i] if i<len(right["operations"]) else None
        if x!=y:
            first={"index":i+1,"observed":x,"reference":y}
            break
    snapshot=_snapshot(a,b,"0"*a.num_qubits,True,max_bytes)
    return {"schema_version":1,"scope":"structural diff and ideal zero-input behavior; strict operator metrics",
            "structure_equal":left==right,"global_phase_difference":left["global_phase"]-right["global_phase"],
            "first_operation_difference":first,
            "gate_counts":[len(left["operations"]),len(right["operations"])],
            "depths":[a._qc.depth(),b._qc.depth()],"zero_input":snapshot,
            "operator":a.test.metrics(b,atol=atol,max_bytes=max_bytes)}
