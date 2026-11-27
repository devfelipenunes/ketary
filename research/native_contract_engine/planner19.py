"""Research-only independent Clifford replay and bounded native route planning.

The independent checker implements Pauli multiplication on X^x Z^z with
a power of i, not the Rust tableau/conjugation equations. No authenticity
or independent non-Clifford certification is implied.
"""
from dataclasses import dataclass
import hashlib, struct
from engine import valid_pauli, difference, product_witness
from native9 import RustSession, bounds, reduce_cone
from sparse import BudgetExceeded

def multiply(a,b):
    x,z,k=a; y,w,j=b
    return x^y,z^w,(k+j+2*((z&y).bit_count()%2))%4

def independent_image(n, packed, post, *, max_work=2_000_000):
    if type(n) is not int or not 1<=n<=64 or type(packed) is not bytes or len(packed)%3 or len(packed)>300_000:
        raise ValueError("snapshot")
    bounds(4096,max_work)
    valid_pauli(post,n)
    g=tuple(tuple(packed[i:i+3]) for i in range(0,len(packed),3))
    for op,a,b in g:
        if op>7 or a>=n or (op==5 and (b>=n or a==b)) or (op!=5 and b!=0):
            raise ValueError("gate")
    if any(op>=6 for op,_,_ in g):return None
    if (2*n+2)*len(g)>max_work:return None
    x,z,r=post; k=((x&z).bit_count()+2*r)%4
    for op,a,b in reversed(g):
        A=1<<a; B=1<<b
        out=(0,0,k)
        for i in range(n):
            w=1<<i
            if x&w:
                image=(w,0,0)
                if i==a:
                    if op==0:image=(0,A,0)
                    elif op==1:image=(A,A,3)
                    elif op==2:image=(A,A,1)
                    elif op==4:image=(A,0,2)
                    elif op==5:image=(A|B,0,0)
                out=multiply(out,image)
        for i in range(n):
            w=1<<i
            if z&w:
                image=(0,w,0)
                if i==a:
                    if op==0:image=(A,0,0)
                    elif op==3:image=(0,A,2)
                if op==5 and i==b:image=(0,A|B,0)
                out=multiply(out,image)
        x,z,k=out
    phase=(k-(x&z).bit_count())%4
    if phase not in (0,2):raise ArithmeticError("non-Hermitian image")
    return x,z,phase//2

def independent_verdict(n, packed, pre, post, *, max_work=2_000_000):
    valid_pauli(pre,n)
    got=independent_image(n,packed,post,max_work=max_work)
    if got is None:return "INCONCLUSIVE"
    return "PASS" if got==pre else "FAIL"

def snapshot_id(n,packed):
    return hashlib.sha256(b"ketary-research/pauli-packed/v3\0"+struct.pack(">BI",n,len(packed)//3)+packed).hexdigest()

@dataclass(frozen=True)
class Attempt:
    route:str
    status:str
    charged:int

@dataclass(frozen=True)
class Plan:
    status:str
    circuit_id:str
    pre:tuple
    post:tuple
    attempts:tuple
    witness:object
    reserved:int

def factor_native(session,pre,post,*,max_terms,max_work):
    """Disconnected components, native propagation, exact product sign.
    Non-Pauli local images remain inconclusive; no false global failure.
    Budget is a conservative logical reservation, not an allocation limit.
    """
    n=session.width; packed=session.packed
    cost=4*len(packed)+4*n
    if cost>=max_work:return "INCONCLUSIVE",None
    remaining=max_work-cost
    parent=list(range(n))
    def root(i):
        while parent[i]!=i:
            i=parent[i]
        return i
    for op,a,b in zip(packed[::3],packed[1::3],packed[2::3]):
        if op==5:parent[root(a)]=root(b)
    groups={}
    for i in range(n):groups.setdefault(root(i),[]).append(i)
    if len(groups)<2:return "INCONCLUSIVE",None
    rows={k:bytearray() for k in groups}
    maps={k:{w:i for i,w in enumerate(v)} for k,v in groups.items()}
    for op,a,b in zip(packed[::3],packed[1::3],packed[2::3]):
        k=root(a);m=maps[k]
        rows[k].extend((op,m[a],m[b] if op==5 else 0))
    sign=pre[2]^post[2]
    for k,wires in groups.items():
        def sub(mask):return sum(((mask>>i)&1)<<j for j,i in enumerate(wires))
        a=(sub(pre[0]),sub(pre[1]),0);b=(sub(post[0]),sub(post[1]),0)
        if remaining<1:return "INCONCLUSIVE",None
        try:r=RustSession(len(wires),bytes(rows[k])).propagate(b,max_terms=max_terms,max_work=remaining)
        except BudgetExceeded:return "INCONCLUSIVE",None
        remaining-=r.work+len(r.terms)+1
        if remaining<0:return "INCONCLUSIVE",None
        d=1<<r.denominator_power
        if r.terms==((a[0],a[1],d,0),):continue
        if r.terms==((a[0],a[1],-d,0),):sign^=1;continue
        return "INCONCLUSIVE",None
    if not sign:return "PASS",None
    if remaining<2*n+3:return "INCONCLUSIVE",None
    return "FAIL",product_witness(n,{pre[:2]:(-2*(-1)**pre[2],0)},0)

def plan_transition(session,pre,post,*,max_terms=4096,max_work=2_000_000):
    """Deterministic fallback; definitive results share the same semantics.
    Each attempt reserves a disjoint slice; unused reservations are not recycled.
    """
    if type(session) is not RustSession:raise TypeError("prepared snapshot")
    bounds(max_terms,max_work)
    n=session.width;valid_pauli(pre,n);valid_pauli(post,n)
    attempts=[];reserved=0
    routes=("direct","cone","factor")
    quotas=(max_work//3,max_work//3,max_work-2*(max_work//3))
    for route,quota in zip(routes,quotas):
        if not quota:continue
        reserved+=quota;w=None;status="INCONCLUSIVE"
        if route=="factor":
            status,w=factor_native(session,pre,post,max_terms=max_terms,max_work=quota)
        else:
            cost=0;backend=session
            if route=="cone":
                cost=3*len(session.packed)//3
                if quota>cost:backend=RustSession(n,reduce_cone(session.packed,post))
            if quota>cost:
                try:r=backend.propagate(post,max_terms=max_terms,max_work=quota-cost)
                except BudgetExceeded:pass
                else:
                    d=difference(r.terms,r.denominator_power,pre)
                    charge=cost+r.work+len(r.terms)+(2*n+3)*len(d)
                    if charge<=quota:
                        status="FAIL" if d else "PASS"
                        if d:w=product_witness(n,d,r.denominator_power)
        attempts.append(Attempt(route,status,quota))
        if status in ("PASS","FAIL"):
            return Plan(status,session.identity,pre,post,tuple(attempts),w,reserved)
    return Plan("INCONCLUSIVE",session.identity,pre,post,tuple(attempts),None,reserved)
