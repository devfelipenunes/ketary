"""Consolidated research contract facade. No public SDK API changes."""
from dataclasses import dataclass,asdict
from engine import Obligation,Report,Witness,SCOPE,digest,valid_pauli
from native9 import RustSession,bounds
from contract_forms11 import Product,On,Transition,spec,CleanAncillas
from subspace10 import clean

@dataclass(frozen=True)
class Invariant:
    observable:object
    def obligation(self,n):
        p=spec(self.observable,n);return Obligation(p,p)

@dataclass(frozen=True)
class BundleReport:
    status:str
    scope:str
    circuit_ids:tuple
    checks:tuple
    def require(self):
        if self.status!="PASS":raise AssertionError(self.status+": "+self.scope)
        return self

def verdict(rs):
    return "FAIL" if any(r.status=="FAIL" for r in rs) else "PASS" if all(r.status=="PASS" for r in rs) else "INCONCLUSIVE"

@dataclass(frozen=True)
class Engine:
    session:RustSession
    @classmethod
    def prepare(cls,circuit):return cls(RustSession.from_circuit(circuit))
    def transitions(self,contracts,*,adaptive=False,max_terms=4096,max_work=2_000_000):
        bounds(max_terms,max_work)
        if type(adaptive) is not bool or type(contracts) is not tuple or not 1<=len(contracts)<=64:raise ValueError("bounded tuple of contracts")
        n=self.session.width;obs=[]
        for c in contracts:
            if type(c) not in (Invariant,Transition):raise TypeError("transition or invariant")
            obs.append(c.obligation(n))
        items=tuple((o.pre,o.post) for o in obs)
        raw=self.session.native.transition_batch(items,max_terms,max_work,adaptive)
        rs=[]
        for o,v in zip(obs,raw):
            if v is None:status,reason,w="INCONCLUSIVE","term/work budget",None
            else:
                ok,w,peak,work=v
                status="PASS" if ok else "FAIL";reason="exact coefficient equality" if ok else "nonzero exact product-state expectation"
                w=None if w is None else Witness(tuple(w[0]),tuple(w[1]),tuple(w[2]),w[3])
            rs.append(Report(status,"rust-batch-cone" if adaptive else "rust-batch",self.session.identity,digest(asdict(o)),SCOPE,reason,w))
        return BundleReport(verdict(rs),SCOPE,(self.session.identity,),tuple(rs))
    def preserve(self,contract,*,max_terms=4096,max_work=2_000_000):
        if type(contract) is not CleanAncillas:raise TypeError("clean ancillas")
        return clean(self.session,contract.wires,max_terms=max_terms,max_work=max_work)
    def equivalent(self,reference,*,adaptive=True,max_terms=4096,max_work=2_000_000):
        """Full unitary equivalence up to phase via all X/Z generators.
        Relative circuit V†U. Witness belongs to that relative operation.
        Strict phase equivalence is deliberately not implied.
        """
        if type(reference) is not Engine or reference.session.width!=self.session.width:raise ValueError("reference")
        n=self.session.width
        if n>32 or len(self.session.packed)+len(reference.session.packed)>300_000:raise ValueError("relative circuit bounds")
        inv=(0,2,1,3,4,5,7,6);v=reference.session.packed
        inverse=bytes(x for i in range(len(v)-3,-1,-3) for x in (inv[v[i]],v[i+1],v[i+2]))
        relative=Engine(RustSession(n,self.session.packed+inverse))
        cs=tuple(Invariant(p) for i in range(n) for p in ((1<<i,0,0),(0,1<<i,0)))
        r=relative.transitions(cs,adaptive=adaptive,max_terms=max_terms,max_work=max_work)
        return BundleReport(r.status,"Full admitted unitary equivalence up to global phase; witnesses for relative V-dagger U",(self.session.identity,reference.session.identity),r.checks)
