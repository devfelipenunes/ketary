"""Reusable numerical snapshot predicates. No implicit simulation."""
import json
from dataclasses import dataclass
from collections.abc import Mapping
from ._result import Result,CheckResult
from ._observable import Observable
from ._validation import _int,_real,_tol,ResourceLimit


@dataclass(frozen=True)
class VerificationReport:
    status: str
    checks: tuple[tuple[str,CheckResult], ...]

    @property
    def scope(self):
        return "requested ideal snapshot properties; not operator equivalence"

    def to_json(self):
        return json.dumps(self.to_dict(),sort_keys=True,allow_nan=False)

    def to_dict(self):
        return {"schema_version":1,"scope":self.scope,
                "status":self.status,"checks":{name:check.to_dict() for name,check in self.checks}}

    def render(self):
        lines=[self.status+" — ideal snapshot properties"]
        for name,check in self.checks:
            lines.append(f"{check.status} {name}: actual={check.actual}, expected={check.expected}, tolerance={check.tolerance}")
        return "\n".join(lines)

    def require(self):
        if self.status!="PASS":
            raise AssertionError(self.render())
        return self


def _evaluate(result,probabilities,expectations,normalized,atol):
    records=[]
    if normalized:
        records.append(("normalized",result.test.normalized(atol=atol)))
    records.extend(("probability:"+label,result.test.probability(label,value,atol=atol))
                   for label,value in probabilities)
    records.extend((_expectation_name(label,result.num_qubits),result.test.expectation(label,value,atol=atol))
                   for label,value in expectations)
    statuses={check.status for _,check in records}
    status="FAIL" if "FAIL" in statuses else "UNSUPPORTED" if not statuses or "UNSUPPORTED" in statuses else "PASS"
    return VerificationReport(status,tuple(records))


def _predicates(values,n,alphabet,low,high):
    if values is None:
        return ()
    if not isinstance(values,Mapping):
        raise TypeError("expected predicate mapping")
    if len(values)>32:
        raise ResourceLimit("predicate limit exceeded")
    result=[]
    for key,value in values.items():
        if not isinstance(key,str) or len(key)!=n or set(key)-set(alphabet):
            raise ValueError("invalid predicate label")
        value=_real(value)
        if not low<=value<=high:
            raise ValueError("predicate target outside range")
        result.append((key,value))
    return tuple(sorted(result))


def _expectation_name(key,n):
    if isinstance(key,Observable):
        return "expectation:observable:"+json.dumps(key.to_dict(n),sort_keys=True,separators=(",",":"),allow_nan=False)
    return "expectation:"+key

def _expectation_predicates(values,n,*,ordered=False):
    """Shared bounded validation for single Paulis and immutable real sums."""
    if values is None:
        return ()
    if not isinstance(values,Mapping):
        raise TypeError("expected expectation mapping")
    if len(values)>32:
        raise ResourceLimit("predicate limit exceeded")
    rows=[]
    seen=set()
    for key,target in values.items():
        if not isinstance(key,Observable):
            if not isinstance(key,str) or len(key)!=n or set(key)-set("IXYZ"):
                raise ValueError("invalid predicate label; use a full-width Pauli string or Observable")
            target=_real(target)
            if not -1<=target<=1:
                raise ValueError("predicate target outside range")
        else:
            target=_real(target)
        name=_expectation_name(key,n)
        if name in seen:
            raise ValueError("duplicate observable predicate after embedding")
        seen.add(name)
        rows.append((key,target))
    return tuple(rows if ordered else sorted(rows,key=lambda item:_expectation_name(item[0],n)))

@dataclass(frozen=True,init=False)
class Contract:
    num_qubits: int
    probabilities: tuple[tuple[str,float], ...]
    expectations: tuple[tuple[str|Observable,float], ...]
    normalized: bool
    atol: float

    def __init__(self,num_qubits,*,probabilities=None,expectations=None,normalized=False,atol=1e-9):
        n=_int(num_qubits,1)
        if n>22:
            raise ResourceLimit("contract width exceeds 22")
        if type(normalized) is not bool:
            raise ValueError("normalized must be bool")
        p=_predicates(probabilities,n,"01",0,1)
        e=_expectation_predicates(expectations,n)
        count=len(p)+len(e)+int(normalized)
        if not count:
            raise ValueError("contract requires at least one predicate")
        if count>32:
            raise ResourceLimit("contract predicate limit exceeded")
        for key,value in (("num_qubits",n),("probabilities",p),("expectations",e),
                          ("normalized",normalized),("atol",_tol(atol))):
            object.__setattr__(self,key,value)

    def verify(self,result):
        if not isinstance(result,Result):
            raise TypeError("expected Result snapshot")
        if result.num_qubits!=self.num_qubits:
            raise ValueError("contract/result width mismatch")
        return _evaluate(result,self.probabilities,self.expectations,self.normalized,self.atol)

    def to_dict(self):
        record={"num_qubits":self.num_qubits,"probabilities":dict(self.probabilities),
                "expectations":{k:v for k,v in self.expectations if isinstance(k,str)},
                "normalized":self.normalized,"atol":self.atol}
        observables=[{"terms":k.to_dict(self.num_qubits),"expected":v}
                     for k,v in self.expectations if isinstance(k,Observable)]
        if observables:
            record["observable_expectations"]=observables
        return record
