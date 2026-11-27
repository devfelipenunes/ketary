"""Direct exact Pauli expectation by memoized DAG contraction.

No materialized dense vector. Only zero-input pure state, exact Clifford+T.
The contraction cost is bounded in node-pair visits, not bigint bit cost.
"""
from dataclasses import dataclass
from dag22 import Arena
from independent20 import pauli,add,iphase,ZERO

def cmul(a,b):
    x,y,z,w=a;u,v,s,t=b
    return (x*u+2*y*v-z*s-2*w*t,
            x*v+y*u-z*t-w*s,
            x*s+2*y*t+z*u+2*w*v,
            x*t+y*s+z*v+w*u)

def conjugate(a):return a[0],a[1],-a[2],-a[3]

@dataclass(frozen=True)
class Expectation:
    status:str
    numerator:tuple|None
    denominator_power:int|None
    visits:int

def expectation(arena,p,*,max_work=2_000_000):
    if type(arena) is not Arena or type(max_work) is not int or not 1<=max_work<=2_000_000:raise ValueError("arena/work")
    x,z,s=pauli(arena.n,p);cache={};visits=0
    class Cap(Exception):pass
    def contract(a,b):
        nonlocal visits
        visits+=1
        if visits>max_work:raise Cap()
        key=(a,b)
        if key in cache:return cache[key]
        l,*aa=arena.nodes[a];m,*bb=arena.nodes[b]
        assert l==m
        if l==0:r=cmul(conjugate(aa[0]),bb[0])
        else:
            bit=1<<(l-1);flip=int(bool(x&bit))
            # Sum over source j: conj(v[j xor x])*v[j]*(-1)^(z.j).
            u=contract(aa[flip],bb[0]);v=contract(aa[1^flip],bb[1])
            r=add(u,iphase(v,2 if z&bit else 0))
        cache[key]=r;return r
    try:r=iphase(contract(arena.root,arena.root),(x&z).bit_count()+2*s)
    except Cap:return Expectation("INCONCLUSIVE",None,None,max_work)
    if r[2:]!=(0,0):raise ArithmeticError("Hermitian expectation must be real")
    k=2*arena.k;a,b=r[:2]
    while k and a%2==b%2==0:a//=2;b//=2;k-=1
    return Expectation("EXACT",(a,b),k,visits)

def eigen_contract(arena,p,*,max_work=2_000_000):
    r=expectation(arena,p,max_work=max_work)
    if r.status=="INCONCLUSIVE":return r.status
    # For a normalized pure state, expectation +1 iff P|psi>=|psi>.
    return "PASS" if r.numerator==(1<<r.denominator_power,0) else "FAIL"
