"""Private research contracts: projected action, sequential transition composition."""
from dataclasses import dataclass,asdict
from native9 import RustSession,bounds
from consolidated12 import Engine,Transition
from engine import Witness,Report,digest,SCOPE as PAULI_SCOPE
from logical14 import SCOPE
from contract_forms11 import spec

def mask_for(n,w):
    if type(w) is not tuple or not w or len(w)>n or any(type(i) is not int or not 0<=i<n for i in w) or len(set(w))!=len(w):raise ValueError("ancillas")
    return sum(1<<i for i in w)

def relative(a,b):
    if type(a) is not Engine or type(b) is not Engine or a.session.width!=b.session.width or len(a.session.packed)+len(b.session.packed)>300_000:raise ValueError("relative input")
    inv=(0,2,1,3,4,5,7,6);v=b.session.packed
    inverse=bytes(x for i in range(len(v)-3,-1,-3) for x in (inv[v[i]],v[i+1],v[i+2]))
    return RustSession(a.session.width,a.session.packed+inverse)

@dataclass(frozen=True)
class ProjectedReport:
    status:str
    scope:str
    circuit_ids:tuple
    ancillas:tuple
    generator:tuple|None
    witness:Witness|None
    work_charged:int
    reason:str
    def require(self):
        if self.status!="PASS":raise AssertionError(self.status+": "+self.reason)
        return self

def projected(s,w,ps,ids,scope,*,max_terms,max_work,adaptive):
    bounds(max_terms,max_work)
    mask=mask_for(s.width,w)
    status,index,raw,work=s.native.projected(tuple((p,p) for p in ps),mask,max_terms,max_work,adaptive)
    witness=None if raw is None else Witness(tuple(raw[0]),tuple(raw[1]),tuple(raw[2]),raw[3])
    if witness is not None:assert all(witness.axes[i]=="Z" and witness.signs[i]==1 for i in w)
    return ProjectedReport(("PASS","FAIL","INCONCLUSIVE")[status],scope,ids,w,None if index==len(ps) else ps[index],witness,work,("all projected generators fixed","compressed generator differs","shared propagation/preprocess budget")[status])

@dataclass(frozen=True)
class Clean:
    ancillas:tuple
    def verify(self,e,*,max_terms=4096,max_work=2_000_000,adaptive=False):
        if type(e) is not Engine:raise TypeError("engine")
        mask_for(e.session.width,self.ancillas)
        ps=tuple((0,1<<i,0) for i in self.ancillas)
        return projected(e.session,self.ancillas,ps,(e.session.identity,),"Exact zero leakage on all clean inputs",max_terms=max_terms,max_work=max_work,adaptive=adaptive)

@dataclass(frozen=True)
class Action:
    ancillas:tuple
    def verify(self,a,b,*,max_terms=4096,max_work=2_000_000,adaptive=True):
        r=relative(a,b);n=r.width;w=self.ancillas;mask=mask_for(n,w)
        ps=tuple((0,1<<i,0) for i in w)+tuple(p for i in range(n) if not mask&(1<<i) for p in ((1<<i,0,0),(0,1<<i,0)))
        return projected(r,w,ps,(a.session.identity,b.session.identity),SCOPE,max_terms=max_terms,max_work=max_work,adaptive=adaptive)

@dataclass(frozen=True)
class CompositionReport:
    status:str
    scope:str
    component_ids:tuple
    local:tuple
    direct:object|None
    reason:str
    def require(self):
        if self.status!="PASS":raise AssertionError(self.status+": "+self.reason)
        return self

def compose(stages,chain,*,max_terms=4096,max_work=2_000_000):
    """For ordered U1..Uk, local U_i† P_i U_i=P_(i-1) prove global identity.
    Local failure is NOT global failure. Direct fallback only with separate budget.
    """
    bounds(max_terms,max_work)
    if type(stages) is not tuple or not 1<=len(stages)<=16 or any(type(e) is not Engine for e in stages) or type(chain) is not tuple or len(chain)!=len(stages)+1:raise ValueError("composition")
    n=stages[0].session.width
    if any(e.session.width!=n for e in stages) or sum(len(e.session.packed) for e in stages)>300_000:raise ValueError("composition bounds")
    ps=tuple(spec(p,n) for p in chain)
    budget=max_work//(len(stages)+1)
    ids=tuple(e.session.identity for e in stages)
    if budget==0:return CompositionReport("INCONCLUSIVE",PAULI_SCOPE,ids,(),None,"partition budget")
    local=tuple(e.transitions((Transition(ps[i],ps[i+1]),),adaptive=True,max_terms=max_terms,max_work=budget).checks[0] for i,e in enumerate(stages))
    if all(r.status=="PASS" for r in local):return CompositionReport("PASS",PAULI_SCOPE,ids,local,None,"exact local transitions compose")
    whole=Engine(RustSession(n,b"".join(e.session.packed for e in stages)))
    direct=whole.transitions((Transition(ps[0],ps[-1]),),adaptive=True,max_terms=max_terms,max_work=budget).checks[0]
    return CompositionReport(direct.status,PAULI_SCOPE,ids,local,direct,"direct fallback; local failures are not global failures")
