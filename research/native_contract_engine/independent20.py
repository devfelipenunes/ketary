"""Independent exact bounded state-vector oracle (not Rust/Pauli propagation).

Each amplitude is (a+b sqrt(2)+i(c+d sqrt(2)))/2**k, integer coefficients.
The global denominator is shared by a column. No numerical tolerance.
Admitted packed Clifford+T alphabet only; no source global-phase guarantee.
"""
from dataclasses import dataclass
from itertools import combinations_with_replacement

ZERO=(0,0,0,0)
ONE=(1,0,0,0)
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def neg(a):return tuple(-x for x in a)
def twice(a):return tuple(2*x for x in a)
def sqrt2(a):
    x,y,z,w=a;return 2*y,x,2*w,z
def iphase(a,k):
    x,y,z,w=a
    return (a,(-z,-w,x,y),(-x,-y,-z,-w),(z,w,-x,-y))[k%4]

def admit(n,g,max_work):
    if type(n) is not int or not 1<=n<=5 or type(g) is not bytes or len(g)%3 or len(g)>1536:
        raise ValueError("bounded exact oracle input")
    if type(max_work) is not int or not 1<=max_work<=2_000_000:raise ValueError("work")
    rows=tuple(zip(g[::3],g[1::3],g[2::3]))
    for op,a,b in rows:
        if op>7 or a>=n or (op==5 and (b>=n or a==b)) or (op!=5 and b!=0):
            raise ValueError("gate")
    return rows

def pauli(n,p):
    if type(n) is not int or not 1<=n<=64 or type(p) is not tuple or len(p)!=3 or any(type(v) is not int for v in p) or not 0<=p[0]<1<<n or not 0<=p[1]<1<<n or p[2] not in (0,1):
        raise ValueError("signed Pauli")
    return p

def column(n,rows,index):
    d=1<<n;v=[ZERO]*d;v[index]=ONE;k=0
    for op,a,b in rows:
        A=1<<a;B=1<<b
        if op==0:
            for j in range(d):
                if not j&A:
                    x,y=v[j],v[j|A]
                    v[j],v[j|A]=sqrt2(add(x,y)),sqrt2(add(x,neg(y)))
            k+=1
        elif op in (6,7):
            for j in range(d):
                if j&A:
                    x=sqrt2(v[j]);v[j]=add(x,iphase(x,1 if op==6 else 3))
                else:v[j]=twice(v[j])
            k+=1
        elif op in (1,2,4):
            for j in range(d):
                if j&A:v[j]=iphase(v[j],{1:1,2:3,4:2}[op])
        elif op in (3,5):
            for j in range(d):
                if op==3 and not j&A:v[j],v[j|A]=v[j|A],v[j]
                elif op==5 and j&A and not j&B:v[j],v[j|B]=v[j|B],v[j]
    return tuple(v),k

def action(v,p):
    x,z,s=p;out=[ZERO]*len(v)
    k=((x&z).bit_count()+2*s)%4
    for j,a in enumerate(v):
        out[j^x]=iphase(a,k+2*((j&z).bit_count()%2))
    return tuple(out)

@dataclass(frozen=True)
class ExactCheck:
    status:str
    input_basis:int|None
    denominator_power:int|None
    first_difference:int|None
    left:tuple|None
    right:tuple|None

def verify_transition(n,g,pre,post,*,max_work=2_000_000):
    """All basis columns: U A = B U, equivalent to U† B U=A.
    A mismatch is an exact operator counterexample, not a state-expectation witness.
    Work cap is an abstract bound on amplitude visits, not integer bit operations.
    """
    rows=admit(n,g,max_work);pauli(n,pre);pauli(n,post)
    d=1<<n
    if d*d*(len(rows)+4)>max_work:return ExactCheck("INCONCLUSIVE",None,None,None,None,None)
    cols=[column(n,rows,j) for j in range(d)]
    x,z,s=pre
    for j,(v,k) in enumerate(cols):
        w,h=cols[j^x];assert k==h
        phase=(x&z).bit_count()+2*s+2*((j&z).bit_count()%2)
        left=tuple(iphase(a,phase) for a in w)
        right=action(v,post)
        if left!=right:
            i=next(i for i,(a,b) in enumerate(zip(left,right)) if a!=b)
            return ExactCheck("FAIL",j,k,i,left[i],right[i])
    return ExactCheck("PASS",None,None,None,None,None)

def bell_target(n,g,a,b,*,max_work=2_000_000):
    """Exact Bell Phi+ target on two wires from |0...0>.
    Both XX and ZZ stabilize the state iff the pair is Phi+ and factors
    from the remaining wires. FAIL means not this target, not separability.
    """
    rows=admit(n,g,max_work)
    if type(a) is not int or type(b) is not int or not 0<=a<n or not 0<=b<n or a==b:raise ValueError("wires")
    if (1<<n)*(len(rows)+3)>max_work:return "INCONCLUSIVE"
    v,_=column(n,rows,0);mask=(1<<a)|(1<<b)
    return "PASS" if action(v,(mask,0,0))==v and action(v,(0,mask,0))==v else "FAIL"

def anticommute(p,q):
    return ((p[0]&q[1]).bit_count()+(p[1]&q[0]).bit_count())%2

def reduce_mask(v,basis):
    while v:
        k=v.bit_length()-1
        if k not in basis:return v
        v^=basis[k]
    return 0

@dataclass(frozen=True)
class CodeCheck:
    status:str
    pair:tuple|None
    checked_pairs:int
    reason:str

def correctable_pauli_set(n,stabilizers,errors,*,max_pairs=4096):
    """Exact Knill-Laflamme criterion for an admitted stabilizer code and
    finite Pauli error set, ignoring irrelevant Pauli phases. A PASS proves
    existence of a recovery for that set, not a particular implementation.
    Independent commuting generators imply a nonempty code space.
    """
    if type(n) is not int or not 1<=n<=64 or type(stabilizers) is not tuple or not 1<=len(stabilizers)<=n or type(errors) is not tuple or not 1<=len(errors)<=128 or type(max_pairs) is not int or not 1<=max_pairs<=8256:raise ValueError("code bounds")
    ss=tuple(pauli(n,p) for p in stabilizers)
    es=tuple(pauli(n,p) for p in errors)
    basis={}
    for i,p in enumerate(ss):
        if any(anticommute(p,q) for q in ss[:i]):raise ValueError("noncommuting")
        v=reduce_mask(p[0]|(p[1]<<n),basis)
        if not v:raise ValueError("dependent generators")
        basis[v.bit_length()-1]=v
    count=0
    for i,j in combinations_with_replacement(range(len(es)),2):
        if count>=max_pairs:return CodeCheck("INCONCLUSIVE",None,count,"pair budget")
        count+=1
        x,z=es[i][0]^es[j][0],es[i][1]^es[j][1]
        if any(anticommute((x,z),p) for p in ss):continue
        if reduce_mask(x|(z<<n),basis):
            return CodeCheck("FAIL",(i,j),count,"nontrivial logical operator in error pair")
    return CodeCheck("PASS",None,count,"Knill-Laflamme for supplied Pauli error set")
