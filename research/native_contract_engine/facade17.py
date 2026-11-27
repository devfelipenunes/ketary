"""One private research facade, preserving existing Observable and Contract APIs."""
from dataclasses import dataclass
import ketary as q
from contract_forms11 import spec,label_mask,Transition
from consolidated12 import Engine,Invariant
from contracts15 import Clean,Action,mask_for
from monomial16 import MonomialAction
from native9 import bounds

def signed(p,n):
    if type(p) is q.Observable:
        # Public Observable supports width <=62; do not silently increase it.
        d=p.to_dict()
        if len(d)!=1:raise ValueError("exact contract requires one signed Pauli")
        label,c=next(iter(d.items()))
        if len(label)>n or c not in (-1.,1.):raise ValueError("signed unit Pauli required")
        return label_mask(("-" if c<0 else "")+label.rjust(n,"I"),n)
    return spec(p,n)

@dataclass(frozen=True)
class ContractSpec:
    kind:str
    pre:object=None
    post:object=None
    ancillas:tuple=()
    @classmethod
    def transition(cls,*,requires,ensures):return cls("transition",requires,ensures)
    @classmethod
    def invariant(cls,p):return cls("invariant",p,p)
    @classmethod
    def clean(cls,*w):return cls("clean",ancillas=w)
    @classmethod
    def action(cls,*w):return cls("action",ancillas=w)
    def canonical(self,n):
        if type(self.kind) is not str:raise ValueError("kind")
        if self.kind in ("transition","invariant"):
            if self.ancillas!=():raise ValueError("unexpected ancillas")
            a,b=signed(self.pre,n),signed(self.post,n)
            if self.kind=="invariant" and a!=b:raise ValueError("invariant")
            return {"kind":self.kind,"pre":a,"post":b}
        if self.kind in ("clean","action"):
            if self.pre is not None or self.post is not None:raise ValueError("unexpected operator")
            mask_for(n,self.ancillas)
            return {"kind":self.kind,"ancillas":self.ancillas}
        raise ValueError("unsupported contract kind")

@dataclass(frozen=True)
class Policy:
    route:str="projected"
    max_terms:int=4096
    max_work:int=2_000_000
    def validate(self,kind):
        bounds(self.max_terms,self.max_work)
        if type(self.route) is not str or self.route not in (("projected","monomial") if kind=="action" else ("projected",)):raise ValueError("explicit route")
        if self.route=="monomial" and self.max_terms!=4096:raise ValueError("term cap not used by monomial route")

def verify(engine,contract,*,reference=None,policy=Policy()):
    if type(engine) is not Engine or type(contract) is not ContractSpec or type(policy) is not Policy:raise TypeError("prepared engine, contract and policy")
    c=contract.canonical(engine.session.width);kind=c["kind"];policy.validate(kind)
    if kind!="action" and reference is not None:raise ValueError("reference only for action")
    if kind in ("transition","invariant"):
        return engine.transitions((Transition(c["pre"],c["post"]),),adaptive=True,max_terms=policy.max_terms,max_work=policy.max_work).checks[0]
    if kind=="clean":
        return Clean(c["ancillas"]).verify(engine,max_terms=policy.max_terms,max_work=policy.max_work)
    if type(reference) is not Engine:raise TypeError("explicit reference")
    if policy.route=="monomial":return MonomialAction(c["ancillas"]).verify(engine,reference,max_work=policy.max_work)
    return Action(c["ancillas"]).verify(engine,reference,max_terms=policy.max_terms,max_work=policy.max_work)
