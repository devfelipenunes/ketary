"""R24: unified private router, compact native witnesses and bounded composition.

Only exact signed Pauli transitions and zero-input state eigencontracts.
The two domains are deliberately separate. Logical budgets are not wall
clock, allocator, or integer bit-operation guarantees.
"""
from dataclasses import dataclass,field
import ketary_native_research as rn
from native9 import RustSession,bounds
from engine import valid_pauli,Witness
from planner19 import plan_transition
from cuts21 import cuts,check_certificate
from certificate23 import encode
from prepared23 import Prepared,Result

@dataclass(frozen=True)
class Compact:
    width:int
    ax:int
    az:int
    negative:int
    value:int
    def expand(self):
        return Witness(tuple("IZXY"[2*((self.ax>>i)&1)+((self.az>>i)&1)] for i in range(self.width)),
                       tuple(-1 if self.negative>>i&1 else 1 for i in range(self.width)),
                       (self.value,0),0)

@dataclass(frozen=True)
class Report:
    status:str
    circuit_id:str
    route:str
    pre:tuple
    post:tuple
    witness:object=None
    certificate:bytes|None=None
    def expanded(self):
        w=self.witness.expand() if type(self.witness) is Compact else self.witness
        return Result(self.status,self.circuit_id,self.route,self.pre,self.post,w)

@dataclass(frozen=True)
class Unified:
    session:RustSession
    max_build_work:int=2_000_000
    prepared:Prepared=field(init=False,repr=False,compare=False)
    def __post_init__(self):
        object.__setattr__(self,"prepared",Prepared(self.session,self.max_build_work))
    def transitions(self,items,*,max_work=2_000_000,composition=True):
        bounds(4096,max_work)
        if type(items) is not tuple or not 1<=len(items)<=64 or type(composition) is not bool:raise ValueError("request")
        s=self.session;n=s.width
        for item in items:
            if type(item) is not tuple or len(item)!=2:raise ValueError("item")
            valid_pauli(item[0],n);valid_pauli(item[1],n)
        def report(a,b,status,route,w=None,c=None):return Report(status,s.identity,route,a,b,w,c)
        t=self.prepared.tableau
        if t is not None:
            raw=t.contracts(items,max_work)
            return tuple(report(a,b,"INCONCLUSIVE","tableau-budget") if r is None else
                         report(a,b,"PASS" if r[0] else "FAIL","tableau-native",Compact(n,*r[1]) if r[1] is not None else None)
                         for (a,b),r in zip(items,raw))
        # Reserve disjoint budgets before attempting exact routes. A failure
        # to generate or verify a certificate cannot become a negative verdict.
        q=max_work//len(items);out=[]
        for a,b in items:
            if not q:
                out.append(report(a,b,"INCONCLUSIVE","budget"));continue
            direct=q if not composition else q//2
            if direct:
                r=plan_transition(s,a,b,max_work=direct)
                if r.status!="INCONCLUSIVE":
                    out.append(report(a,b,r.status,"planner",r.witness));continue
            if composition:
                remainder=q-direct;produce=remainder//2;check=remainder-produce
                # The producer is a bounded search with one deterministic cut
                # width. Checker is independent of native propagation.
                if produce and check:
                    c=cuts(s,a,b,chunk=4,max_work=produce)
                    if c is not None and check_certificate(n,s.packed,a,b,c,max_work=check):
                        out.append(report(a,b,"PASS","temporal-certificate",c=encode(c)));continue
            out.append(report(a,b,"INCONCLUSIVE","exhausted"))
        return tuple(out)
