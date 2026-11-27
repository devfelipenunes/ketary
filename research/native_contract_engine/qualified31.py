"""Additional typed domains: exact rational sums, Pauli noise and finite QEC.
Uses R30 for existing contracts. QEC checks the supplied code/error set,
not the prepared circuit; no physical recovery or arbitrary noise claim.
"""
from dataclasses import dataclass
from fractions import Fraction
from qualified30 import Engine as Base,Report,validate as base_validate
from candidate28 import Policy
from native9 import RustSession,bounds
from independent20 import pauli,correctable_pauli_set
from structures21 import recovery_table
from contracts18 import exact_sum,admit_sum
from noise17 import PauliNoise,NoiseTransition
from consolidated12 import Engine as Legacy
from engine import digest

@dataclass(frozen=True)
class SumTransition:
    pre:tuple
    post:tuple

@dataclass(frozen=True)
class NoiseAfter:
    pre:tuple
    post:tuple
    entries:tuple
    denominator:int
    coefficient:Fraction=Fraction(1)

@dataclass(frozen=True)
class Correctable:
    stabilizers:tuple
    errors:tuple

def rational(f,limit=64):
    if type(f) is not Fraction or max(abs(f.numerator).bit_length(),f.denominator.bit_length())>limit:raise ValueError("bounded rational")
    return [f.numerator,f.denominator]

def sum_terms(n,ts):
    if type(ts) is not tuple or not 1<=len(ts)<=64:raise ValueError("sum")
    out=[]
    for t in ts:
        if type(t) is not tuple or len(t)!=2:raise ValueError("term")
        p,c=t;pauli(n,p);out.append([p,rational(c)])
    return out

def validate(s,x):
    n=s.width;ids=(s.identity,)
    if type(x) is SumTransition:
        domain="all-input-rational-pauli-sum"
        body={"pre":sum_terms(n,x.pre),"post":sum_terms(n,x.post)}
    elif type(x) is NoiseAfter:
        pauli(n,x.pre);pauli(n,x.post)
        if type(x.entries) is not tuple or not 1<=len(x.entries)<=16:raise ValueError("mixture")
        for e in x.entries:
            if type(e) is not tuple or len(e)!=2:raise ValueError("entry")
            pauli(n,e[0])
        PauliNoise(x.entries,x.denominator).admitted(n)
        co=rational(x.coefficient,257)
        if abs(x.coefficient)>1:raise ValueError("coefficient")
        domain="all-input-clifford-then-pauli-mixture"
        body={"pre":x.pre,"post":x.post,"entries":x.entries,"denominator":x.denominator,"coefficient":co}
    elif type(x) is Correctable:
        # Validate full generator independence, commutation and error admission
        # using the bounded first-pair check. No dependence on circuit gates.
        correctable_pauli_set(n,x.stabilizers,x.errors,max_pairs=1)
        domain="finite-pauli-error-set-correctability"
        ids=()
        body={"width":n,"stabilizers":x.stabilizers,"errors":x.errors}
    else:return base_validate(s,x)
    return domain,ids,digest({"domain":domain,"snapshots":ids,"body":body})

@dataclass(frozen=True)
class Engine:
    base:Base
    def __post_init__(self):
        if type(self.base) is not Base:raise TypeError("base")
    @classmethod
    def prepare(cls,s,policy=Policy()):
        return cls(Base.prepare(s,policy))
    def verify(self,items,*,max_work=2_000_000):
        bounds(4096,max_work)
        if type(items) is not tuple or not 1<=len(items)<=64:raise ValueError("items")
        # Base-only requests have identical admission, identity and
        # reservations in R30. Delegate once, without duplicate hashes.
        if all(type(x) not in (SumTransition,NoiseAfter,Correctable) for x in items):
            return self.base.verify(items,max_work=max_work)
        s=self.base.prepared.session;n=s.width;legacy=Legacy(s)
        keys=tuple(validate(s,x) for x in items)
        q=max_work//len(items);out=[]
        indices=tuple(i for i,x in enumerate(items) if type(x) not in (SumTransition,NoiseAfter,Correctable))
        base_reports={}
        if q and indices:
            base_reports=dict(zip(indices,self.base.verify(tuple(items[i] for i in indices),max_work=q*len(indices))))
        for idx,(x,(domain,ids,oid)) in enumerate(zip(items,keys)):
            def report(status,detail=None):return Report(status,domain,ids,oid,q,detail)
            if not q:out.append(report("INCONCLUSIVE"));continue
            if type(x) is SumTransition:
                r=exact_sum(legacy,x.pre,x.post,max_work=q)
            elif type(x) is NoiseAfter:
                if any(op>=6 for op in s.packed[::3]):out.append(report("UNSUPPORTED"));continue
                # Reserve diagnostic and admission visits separately.
                reserve=8*n+len(x.entries)+32
                if reserve>=q:out.append(report("INCONCLUSIVE"));continue
                r=NoiseTransition(x.pre,x.post,x.coefficient).verify(n,(legacy,PauliNoise(x.entries,x.denominator)),max_work=q-reserve)
            elif type(x) is Correctable:
                m=len(x.stabilizers);k=len(x.errors)
                # Logical upper reservation for generator preflight, pair
                # commutation/reduction and syndrome table construction.
                overhead=(m*m+k*m+1)*(n+1)
                per_pair=(m+2*n+1)
                cap=min(8256,max(0,(q-overhead)//per_pair))
                if not cap:out.append(report("INCONCLUSIVE"));continue
                r=recovery_table(n,x.stabilizers,x.errors,max_pairs=cap)
            else:
                out.append(base_reports[idx]);continue
            out.append(report(r.status,r))
        return tuple(out)
