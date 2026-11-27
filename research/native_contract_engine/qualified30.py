"""R30 typed multi-domain adapter; no public SDK changes.

All-input transitions and zero-input eigencontracts use candidate28.
Projected, relative and bounded exact column semantics reuse their
qualified implementations. No numerical results promoted to exact.
"""
from dataclasses import dataclass
from candidate28 import Engine as Prepared,Transition,StateEigen,Policy,obligation,Report as CoreReport
from router27 import Attempt
from unified24 import Compact
from consolidated12 import Engine as Legacy
from contracts15 import Clean,Action,mask_for
from monomial16 import action
from semantics25 import separable,strict_equal,z_instrument
from independent20 import pauli
from native9 import RustSession,bounds
from engine import digest

@dataclass(frozen=True)
class CleanInput:
    ancillas:tuple

@dataclass(frozen=True)
class RelativeAction:
    reference:RustSession
    ancillas:tuple

@dataclass(frozen=True)
class Equivalent:
    reference:RustSession
    strict:bool=False

@dataclass(frozen=True)
class Separable:
    cut:int

@dataclass(frozen=True)
class ZBranch:
    wire:int
    outcome:int
    observable:tuple
    probability:tuple
    expectation:tuple

@dataclass(frozen=True)
class Report:
    status:str
    domain:str
    snapshots:tuple
    obligation:str
    reserved:int
    detail:object=None

def rational(x):
    # Exact dyadic Q(sqrt2) value, bounded and canonical.
    if type(x) is not tuple or len(x)!=2 or type(x[0]) is not tuple or len(x[0])!=2 or any(type(v) is not int or abs(v).bit_length()>1024 for v in x[0]) or type(x[1]) is not int or not 0<=x[1]<=1024:raise ValueError("exact coefficient")
    a,b=x[0];k=x[1]
    if k and a%2==b%2==0:raise ValueError("noncanonical coefficient")
    return x

def norm(a,k):
    a,b=a
    while k and a%2==b%2==0:a//=2;b//=2;k-=1
    return ((a,b),k)

def validate(s,x):
    n=s.width;ids=(s.identity,)
    if type(x) in (Transition,StateEigen):
        domain,oid=obligation(n,x);return domain,ids,oid
    if type(x) is CleanInput:
        mask_for(n,x.ancillas);domain="all-clean-input-leakage";body={"ancillas":sorted(x.ancillas)}
    elif type(x) in (RelativeAction,Equivalent):
        r=x.reference
        if type(r) is not RustSession or r.width!=n:raise ValueError("reference")
        ids+=(r.identity,)
        if type(x) is RelativeAction:
            mask_for(n,x.ancillas);domain="clean-input-coherent-action-up-to-phase";body={"ancillas":sorted(x.ancillas)}
        else:
            if type(x.strict) is not bool:raise ValueError("strict")
            domain="packed-strict-unitary" if x.strict else "packed-unitary-up-to-phase";body={}
    elif type(x) is Separable:
        if type(x.cut) is not int or not 0<x.cut<(1<<n)-1:raise ValueError("cut")
        domain="zero-input-pure-bipartite-separability";body={"cut":x.cut}
    elif type(x) is ZBranch:
        if type(x.wire) is not int or not 0<=x.wire<n or type(x.outcome) is not int or x.outcome not in (0,1):raise ValueError("branch")
        pauli(n,x.observable);rational(x.probability);rational(x.expectation)
        domain="zero-input-unnormalized-z-branch";body={"wire":x.wire,"outcome":x.outcome,"observable":x.observable,"probability":x.probability,"expectation":x.expectation}
    else:raise TypeError("explicit contract domain")
    return domain,ids,digest({"domain":domain,"snapshots":ids,"body":body})

@dataclass(frozen=True)
class Engine:
    prepared:Prepared
    def __post_init__(self):
        if type(self.prepared) is not Prepared:raise TypeError("prepared engine")
    @classmethod
    def prepare(cls,s,policy=Policy()):
        return cls(Prepared(s,policy))
    def verify(self,items,*,max_work=2_000_000):
        bounds(4096,max_work)
        if type(items) is not tuple or not 1<=len(items)<=64:raise ValueError("bounded tuple")
        s=self.prepared.session;n=s.width
        keys=tuple(validate(s,x) for x in items)
        q=max_work//len(items);out=[]
        # The fully validated all-transition Clifford path can emit the same
        # report directly from native compact verdicts. No duplicate digest,
        # router, or intermediate report allocations. Per-item admission
        # uses exactly the native cost formula, including witness reservation.
        # A budget-exhausted item does not consume its neighbors' quota.
        tableau=self.prepared.router.previous.prepared.tableau
        if tableau is not None and all(type(x) is Transition for x in items):
            if not q:
                return tuple(Report("INCONCLUSIVE",d,ids,oid,0) for d,ids,oid in keys)
            accepted=tuple(i for i,x in enumerate(items)
                           if 1+x.post[0].bit_count()+x.post[1].bit_count()+2*(2*n+3)<=q)
            raw=tableau.contracts(tuple((items[i].pre,items[i].post) for i in accepted),q*len(accepted)) if accepted else ()
            answers=dict(zip(accepted,raw))
            for i,(domain,ids,oid) in enumerate(keys):
                v=answers.get(i)
                if v is None:
                    status="INCONCLUSIVE";route="tableau-budget";w=None
                else:
                    status="PASS" if v[0] else "FAIL";route="tableau-native"
                    w=Compact(n,*v[1]) if v[1] is not None else None
                detail=CoreReport(status,domain,s.identity,oid,route,witness=w,
                                  attempts=(Attempt(route,status,0),))
                out.append(Report(status,domain,ids,oid,q,detail))
            return tuple(out)
        legacy=Legacy(s)
        # Batch only when each reserved slice covers even the worst-case
        # tableau query + compact witness. Otherwise preserve independent
        # per-obligation exhaustion semantics (no pooled budget borrowing).
        indices=tuple(i for i,x in enumerate(items) if type(x) is Transition)
        fast={}
        if len(indices)>1 and self.prepared.router.previous.prepared.tableau is not None and q>=6*n+7:
            batch=self.prepared.verify(tuple(items[i] for i in indices),max_work=q*len(indices))
            fast=dict(zip(indices,batch.reports))
        for idx,(x,(domain,ids,oid)) in enumerate(zip(items,keys)):
            def report(status,detail=None):return Report(status,domain,ids,oid,q,detail)
            if not q:out.append(report("INCONCLUSIVE"));continue
            if type(x) in (Transition,StateEigen):
                r=fast[idx] if idx in fast else self.prepared.verify((x,),max_work=q).reports[0];out.append(report(r.status,r));continue
            if type(x) is CleanInput:r=Clean(x.ancillas).verify(legacy,max_work=q)
            elif type(x) is RelativeAction:
                if len(s.packed)+len(x.reference.packed)>300000:out.append(report("UNSUPPORTED"));continue
                r=action(legacy,Legacy(x.reference),x.ancillas,max_work=q)
            elif type(x) is Equivalent:
                if x.strict:
                    if n>5 or max(len(s.packed),len(x.reference.packed))>1536:out.append(report("UNSUPPORTED"));continue
                    r=strict_equal(n,s.packed,x.reference.packed,max_work=q)
                else:
                    if n>32 or len(s.packed)+len(x.reference.packed)>300000:out.append(report("UNSUPPORTED"));continue
                    r=legacy.equivalent(Legacy(x.reference),max_work=q)
            elif type(x) is Separable:
                if n>5 or len(s.packed)>1536:out.append(report("UNSUPPORTED"));continue
                r=separable(n,s.packed,x.cut,max_work=q)
            else:
                if n>5 or len(s.packed)>1536:out.append(report("UNSUPPORTED"));continue
                r=z_instrument(n,s.packed,x.observable,x.wire,x.outcome,max_work=q)
                if r is None:out.append(report("INCONCLUSIVE"));continue
                a,b,k=r;got=(norm(a,k),norm(b,k))
                out.append(report("PASS" if got==(x.probability,x.expectation) else "FAIL",got));continue
            out.append(report(r.status,r))
        return tuple(out)
