"""R23 prepared exact Clifford contract dispatch with bound snapshot provenance.

Preparation and query budgets are distinct. No public SDK change.
"""
from dataclasses import dataclass,field
import ketary_native_research as rn
from native9 import RustSession,bounds
from engine import valid_pauli,product_witness
from planner19 import plan_transition

@dataclass(frozen=True)
class Result:
    status:str
    circuit_id:str
    route:str
    pre:tuple
    post:tuple
    witness:object

@dataclass(frozen=True)
class Prepared:
    session:RustSession
    max_build_work:int=2_000_000
    tableau:object=field(init=False,repr=False,compare=False)
    def __post_init__(self):
        if type(self.session) is not RustSession:raise TypeError("snapshot")
        bounds(4096,self.max_build_work)
        t=None
        if all(op<6 for op in self.session.packed[::3]):
            try:t=rn.CliffordTableau(self.session.native,self.max_build_work)
            except rn.BudgetExceeded:pass
        object.__setattr__(self,"tableau",t)
    def transitions(self,items,*,max_work=2_000_000,workers=1):
        bounds(4096,max_work)
        if type(items) is not tuple or not 1<=len(items)<=64 or type(workers) is not int or not 1<=workers<=8:raise ValueError("items/workers")
        n=self.session.width
        for item in items:
            if type(item) is not tuple or len(item)!=2:raise ValueError("item")
            valid_pauli(item[0],n);valid_pauli(item[1],n)
        out=[];rem=max_work
        def result(a,b,status,route,w=None):return Result(status,self.session.identity,route,a,b,w)
        if self.tableau is not None:
            # Reserve worst-case witness work for two Pauli terms before
            # querying each item, preserving deterministic budget prefix.
            admitted=[]
            for a,b in items:
                cost=1+b[0].bit_count()+b[1].bit_count()+2*(2*n+3)
                if cost>rem:break
                rem-=cost;admitted.append((a,b))
            images=self.tableau.images(tuple(b for a,b in admitted),workers,max_work) if admitted else ()
            for (a,b),p in zip(admitted,images):
                if a==p:out.append(result(a,b,"PASS","tableau"));continue
                d={p[:2]:((-1)**p[2],0)}
                old=d.get(a[:2],(0,0));d[a[:2]]=(old[0]-(-1)**a[2],0)
                d={k:v for k,v in d.items() if v!=(0,0)}
                out.append(result(a,b,"FAIL","tableau",product_witness(n,d,0)))
            out.extend(result(a,b,"INCONCLUSIVE","tableau-budget") for a,b in items[len(admitted):])
        else:
            # Disjoint reservations for fallback, no recycling across items.
            quota=max_work//len(items)
            for a,b in items:
                if quota:
                    r=plan_transition(self.session,a,b,max_work=quota)
                    out.append(result(a,b,r.status,"planner",r.witness))
                else:out.append(result(a,b,"INCONCLUSIVE","planner-budget"))
        return tuple(out)
