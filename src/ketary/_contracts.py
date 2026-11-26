"""Reusable numerical snapshot predicates. No implicit simulation."""
from dataclasses import dataclass
from collections.abc import Mapping
from ._result import Result,CheckResult
from ._validation import _int,_real,_tol,ResourceLimit


@dataclass(frozen=True)
class VerificationReport:
    status: str
    checks: tuple[tuple[str,CheckResult], ...]

    def to_dict(self):
        return {"schema_version":1,"scope":"requested ideal snapshot properties; not operator equivalence",
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
    records.extend(("expectation:"+label,result.test.expectation(label,value,atol=atol))
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


@dataclass(frozen=True,init=False)
class Contract:
    num_qubits: int
    probabilities: tuple[tuple[str,float], ...]
    expectations: tuple[tuple[str,float], ...]
    normalized: bool
    atol: float

    def __init__(self,num_qubits,*,probabilities=None,expectations=None,normalized=False,atol=1e-9):
        n=_int(num_qubits,1)
        if n>22:
            raise ResourceLimit("contract width exceeds 22")
        if type(normalized) is not bool:
            raise ValueError("normalized must be bool")
        p=_predicates(probabilities,n,"01",0,1)
        e=_predicates(expectations,n,"IXYZ",-1,1)
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
        return {"num_qubits":self.num_qubits,"probabilities":dict(self.probabilities),
                "expectations":dict(self.expectations),"normalized":self.normalized,"atol":self.atol}
