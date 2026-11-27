"""Exact coherent action on a declared clean input subspace; research only."""
from dataclasses import dataclass,asdict
from native9 import RustSession,bounds
from consolidated12 import Engine
from engine import _add,product_witness,Report,digest
from sparse import BudgetExceeded

SCOPE="Full coherent action on all clean-input states, up to one common global phase; relative V-dagger U; admitted unitary alphabet"
@dataclass(frozen=True)
class LogicalAction:
    ancillas:tuple
    def verify(self,actual,reference,*,max_terms=4096,max_work=2_000_000):
        bounds(max_terms,max_work)
        if type(actual) is not Engine or type(reference) is not Engine or actual.session.width!=reference.session.width:raise ValueError("engines")
        n=actual.session.width;w=self.ancillas
        if type(w) is not tuple or not w or len(w)>n or any(type(i) is not int or not 0<=i<n for i in w) or len(set(w))!=len(w):raise ValueError("ancillas")
        if len(actual.session.packed)+len(reference.session.packed)>300_000:raise ValueError("relative gate cap")
        inv=(0,2,1,3,4,5,7,6);v=reference.session.packed
        inverse=bytes(x for i in range(len(v)-3,-1,-3) for x in (inv[v[i]],v[i+1],v[i+2]))
        relative=RustSession(n,actual.session.packed+inverse)
        mask=sum(1<<i for i in w)
        generators=tuple((0,1<<i,0) for i in w)+tuple(p for i in range(n) if i not in w for p in ((1<<i,0,0),(0,1<<i,0)))
        identity=digest({"actual":actual.session.identity,"reference":reference.session.identity,"ancillas":sorted(w),"scope":SCOPE})
        def report(status,reason,witness=None):
            return Report(status,"logical-projected",identity,digest({"ancillas":sorted(w),"scope":SCOPE}),SCOPE,reason,witness)
        remaining=max_work
        for p in generators:
            if remaining<=0:return report("INCONCLUSIVE","aggregate term-work budget")
            # The exact causal reduction is performed by the existing portable helper;
            # charge preprocessing separately. No numerical fallback.
            from native9 import reduce_cone
            cost=3*(len(relative.packed)//3)
            if cost>=remaining:return report("INCONCLUSIVE","preprocess budget")
            remaining-=cost
            reduced=RustSession(n,reduce_cone(relative.packed,p))
            try:r=reduced.propagate(p,max_terms=max_terms,max_work=remaining)
            except BudgetExceeded:return report("INCONCLUSIVE","propagation budget")
            remaining-=r.work;d={}
            for x,z,a,b in r.terms:
                if not x&mask:_add(d,(x,z&~mask),a,b)
            _add(d,(p[0],p[1]&~mask),-(1<<r.denominator_power),0)
            if d:
                wit=product_witness(n,d,r.denominator_power)
                assert all(wit.axes[i]=="Z" and wit.signs[i]==1 for i in w)
                return report("FAIL",f"relative compressed generator {p} differs",wit)
        return report("PASS","relative clean subspace preserved and all data generators fixed")
