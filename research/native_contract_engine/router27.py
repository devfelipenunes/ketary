"""Opt-in unified transition router with bounded spatial replay fallback."""
from dataclasses import dataclass,field
from unified24 import Unified,Report
from native9 import RustSession,bounds
from independent20 import pauli
from spatial_evidence27 import produce,replay

@dataclass(frozen=True)
class Attempt:
    route:str
    status:str
    reserved:int
    used:int|None=None

@dataclass(frozen=True)
class Decision:
    report:Report
    attempts:tuple
    reserved:int
    shared_batch_budget:int|None=None

@dataclass(frozen=True)
class Router:
    session:RustSession
    max_build_work:int=2_000_000
    previous:Unified=field(init=False,repr=False)
    def __post_init__(self):
        object.__setattr__(self,"previous",Unified(self.session,self.max_build_work))
    def transitions(self,items,*,max_work=2_000_000,spatial=True):
        bounds(4096,max_work)
        if type(items) is not tuple or not 1<=len(items)<=64 or type(spatial) is not bool:raise ValueError("request")
        n=self.session.width;g=self.session.packed
        for item in items:
            if type(item) is not tuple or len(item)!=2:raise ValueError("item")
            pauli(n,item[0]);pauli(n,item[1])
        # Preserve the existing batched tableau path and its prefix budget.
        if self.previous.prepared.tableau is not None or not spatial:
            return tuple(Decision(r,(Attempt(r.route,r.status,0),),0,max_work)
                         for r in self.previous.transitions(items,max_work=max_work))
        q=max_work//len(items);out=[]
        part=tuple((i,) for i in range(n))
        for a,b in items:
            attempts=[];old=q//2;sp=q-old
            if old:
                r=self.previous.transitions(((a,b),),max_work=old)[0]
                attempts.append(Attempt(r.route,r.status,old))
                if r.status!="INCONCLUSIVE":
                    out.append(Decision(r,tuple(attempts),old));continue
            # A portable receipt is a replay recipe. The exact spatial
            # producer is independent of Rust; no claim of succinct proof.
            if sp and len(g)<=12288:
                r=produce(n,g,a,b,part,max_work=sp)
                attempts.append(Attempt("spatial",r.status,sp,r.ledger.used))
                if r.status!="INCONCLUSIVE":
                    report=Report(r.status,self.session.identity,"spatial",a,b,r.witness,r.record)
                    out.append(Decision(report,tuple(attempts),sum(t.reserved for t in attempts)));continue
            report=Report("INCONCLUSIVE",self.session.identity,"exhausted",a,b)
            out.append(Decision(report,tuple(attempts),sum(t.reserved for t in attempts)))
        return tuple(out)
