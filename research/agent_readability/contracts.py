"""I02/I05: immutable snapshot contracts and a shared report model.

Research only. No implicit execution, no formal verification claim.
"""
from dataclasses import dataclass
from collections.abc import Mapping
from hashlib import sha256
import json
import math
from numbers import Real
import ketary as q


def _json(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)


def _real(value,low,high):
    if isinstance(value,bool) or not isinstance(value,Real):
        raise ValueError("expected a finite real number")
    value=float(value)
    if not math.isfinite(value) or not low<=value<=high:
        raise ValueError("number outside allowed range")
    return value


def _items(values,alphabet,low,high):
    if values is None:
        return ()
    if not isinstance(values,Mapping) or len(values)>32:
        raise ValueError("expected a mapping with at most 32 entries")
    result=[]
    for key,value in values.items():
        if type(key) is not str or not 1<=len(key)<=22 or set(key)-set(alphabet):
            raise ValueError("invalid property label")
        result.append((key,_real(value,low,high)))
    return tuple(sorted(result))


@dataclass(frozen=True)
class Report:
    """Canonical JSON snapshot; human rendering is derived, not re-computed."""
    _payload: str

    @classmethod
    def from_data(cls,data):
        return cls(_json(data))

    def to_dict(self):
        return json.loads(self._payload)

    def compact_json(self):
        return self._payload

    def render(self):
        data=self.to_dict()
        lines=[f"{data['status']} | {data['scope']}"]
        for key,record in data.get("checks",{}).items():
            lines.append(f"{record['status']} {key}: actual={record.get('actual')}, "
                         f"expected={record.get('expected')}, tolerance={record.get('tolerance')}")
        if "reason" in data:
            lines.append(data["reason"])
        return "\n".join(lines)


@dataclass(frozen=True,init=False)
class Contract:
    num_qubits: int
    probabilities: tuple
    expectations: tuple
    normalized: bool
    atol: float

    def __init__(self,num_qubits,*,probabilities=None,expectations=None,normalized=False,atol=1e-9):
        if type(num_qubits) is not int or not 1<=num_qubits<=22:
            raise ValueError("invalid width")
        if type(normalized) is not bool:
            raise ValueError("normalized must be boolean")
        p=_items(probabilities,"01",0,1)
        e=_items(expectations,"IXYZ",-1,1)
        if not 1<=len(p)+len(e)+int(normalized)<=32:
            raise ValueError("contract needs 1..32 predicates")
        if any(len(key)!=num_qubits for key,_ in p+e):
            raise ValueError("label width mismatch")
        object.__setattr__(self,"num_qubits",num_qubits)
        object.__setattr__(self,"probabilities",p)
        object.__setattr__(self,"expectations",e)
        object.__setattr__(self,"normalized",normalized)
        object.__setattr__(self,"atol",_real(atol,0,1))

    def to_dict(self):
        return {"schema_version":1,"scope":"ideal result snapshot; not operator equivalence",
                "num_qubits":self.num_qubits,"probabilities":dict(self.probabilities),
                "expectations":dict(self.expectations),"normalized":self.normalized,"atol":self.atol}

    def verify(self,result):
        if not isinstance(result,q.Result):
            raise TypeError("expected an explicit Result snapshot")
        if result.num_qubits!=self.num_qubits:
            raise ValueError("snapshot width mismatch")
        data=result.verify(probabilities=dict(self.probabilities),
                           expectations=dict(self.expectations),normalized=self.normalized,atol=self.atol)
        data["scope"]="ideal result snapshot; not operator equivalence"
        data["contract_sha256"]=sha256(_json(self.to_dict()).encode()).hexdigest()
        return Report.from_data(data)
