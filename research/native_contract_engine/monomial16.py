"""Exact bounded monomial action with an explicit specialized route."""
from dataclasses import dataclass
from contracts15 import Action,mask_for
from consolidated12 import Engine
from native9 import bounds

@dataclass(frozen=True)
class MonomialReport:
    status:str
    scope:str
    circuit_ids:tuple
    ancillas:tuple
    reason:str
    evidence:tuple|None
    work_charged:int
    def require(self):
        if self.status!="PASS":raise AssertionError(self.status+": "+self.reason)
        return self

@dataclass(frozen=True)
class MonomialAction:
    ancillas:tuple
    def verify(self,a,b,*,max_work=2_000_000):
        bounds(4096,max_work)
        if type(a) is not Engine or type(b) is not Engine or a.session.width!=b.session.width:raise ValueError("engines")
        mask=mask_for(a.session.width,self.ancillas)
        status,reason,evidence,work=a.session.native.monomial_action(b.session.native,mask,max_work)
        return MonomialReport(("PASS","FAIL","INCONCLUSIVE","UNSUPPORTED")[status],"Exact coherent clean-input action up to common global phase; recognized monomial gates, union interaction components",(a.session.identity,b.session.identity),self.ancillas,reason,evidence,work)

def action(a,b,w,*,max_work=2_000_000):
    # Explicit bounded planner. A specialized failure is decisive. Unsupported
    # or inconclusive may fall back without exceeding the declared allocation.
    bounds(4096,max_work)
    first=max_work//2
    if first==0:return Action(w).verify(a,b,max_work=max_work)
    r=MonomialAction(w).verify(a,b,max_work=first)
    return r if r.status in ("PASS","FAIL") else Action(w).verify(a,b,max_work=max_work-first)
