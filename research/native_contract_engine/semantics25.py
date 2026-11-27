"""Additional exact bounded semantic contracts; independent state-column oracle."""
from dataclasses import dataclass
from independent20 import admit,column,pauli
from expectation23 import cmul

@dataclass(frozen=True)
class Check:
    status:str
    detail:str
    witness:tuple|None=None

def separable(n,g,mask,*,max_work=2_000_000):
    """Bipartite pure-state separability iff amplitude matrix has rank one.
    FAIL is exact entanglement across this specific cut, not mixed-state entanglement.
    """
    rows=admit(n,g,max_work)
    if type(mask) is not int or not 0<mask<(1<<n)-1:raise ValueError("cut")
    d=1<<n
    if d*(len(rows)+8)>max_work:return Check("INCONCLUSIVE","work")
    v,k=column(n,rows,0);p=next(i for i,a in enumerate(v) if any(a));ref=v[p]
    other=((1<<n)-1)^mask
    for j in range(d):
        a=(j&mask)|(p&other);b=(p&mask)|(j&other)
        if cmul(v[j],ref)!=cmul(v[a],v[b]):
            return Check("FAIL","nonzero 2x2 minor",(j,p,a,b))
    return Check("PASS","rank one across requested cut")

def strict_equal(n,g,h,*,max_work=2_000_000):
    """Strict packed unitary equality including phase induced by the gates.
    No source circuit global-phase metadata is admitted here."""
    a=admit(n,g,max_work);b=admit(n,h,max_work);d=1<<n
    if d*d*(len(a)+len(b)+4)>max_work:return Check("INCONCLUSIVE","work")
    for j in range(d):
        v,k=column(n,a,j);w,l=column(n,b,j)
        for i,(x,y) in enumerate(zip(v,w)):
            if tuple(c<<l for c in x)!=tuple(c<<k for c in y):
                return Check("FAIL","strict amplitude mismatch",(j,i))
    return Check("PASS","all exact packed columns equal")

def z_instrument(n,g,post,wire,outcome,*,max_work=2_000_000):
    """Exact numerator of unnormalized branch expectation after measuring Z.
    On zero input, returns probability and Tr(Pi rho Pi P); no postselection
    division, and zero-probability branches are explicit. No feedback yet."""
    from independent20 import ZERO,add,action
    from expectation23 import conjugate
    rows=admit(n,g,max_work);pauli(n,post)
    if type(wire) is not int or not 0<=wire<n or type(outcome) is not int or outcome not in (0,1):raise ValueError("branch")
    d=1<<n
    if d*(len(rows)+4)>max_work:return None
    v,k=column(n,rows,0)
    w=tuple(a if (i>>wire)&1==outcome else ZERO for i,a in enumerate(v))
    def inner(a,b):
        r=ZERO
        for x,y in zip(a,b):r=add(r,cmul(conjugate(x),y))
        assert r[2:]==(0,0)
        return r[:2]
    return inner(w,w),inner(w,action(w,post)),2*k
