"""Exact zero-input state expectation from Heisenberg propagation.

This does not materialize a state DAG. Use a bounded causal cone and
evaluate each Pauli on |0...0>. Work counts logical visits, not CPU cycles.
"""
from dataclasses import dataclass
from native9 import RustSession,bounds,reduce_cone
from independent20 import pauli
from sparse import BudgetExceeded

@dataclass(frozen=True)
class Result:
    status:str
    expectation:tuple|None
    reserved:int
    used:int

def verify(s,p,*,max_work=2_000_000):
    if type(s) is not RustSession:raise TypeError("session")
    bounds(4096,max_work);pauli(s.width,p)
    scan=3*len(s.packed)//3
    if scan>=max_work:return Result("INCONCLUSIVE",None,max_work,0)
    reduced=reduce_cone(s.packed,p)
    # Reserve the full maximum final coefficient visit count conservatively.
    remain=max_work-scan
    reserve=min(4096,remain//2)
    if not reserve or remain<=reserve:return Result("INCONCLUSIVE",None,max_work,scan)
    try:r=RustSession(s.width,reduced).propagate(p,max_terms=reserve,max_work=remain-reserve)
    except BudgetExceeded:return Result("INCONCLUSIVE",None,max_work,max_work)
    a=b=0
    for x,z,u,v in r.terms:
        if not x:a+=u;b+=v
    k=r.denominator_power
    while k and a%2==b%2==0:a//=2;b//=2;k-=1
    return Result("PASS" if (a,b)==(1<<k,0) else "FAIL",((a,b),k),max_work,scan+r.work+len(r.terms))
