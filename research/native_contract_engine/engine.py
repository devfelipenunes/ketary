"""Research-only exact Pauli transition engine, no public API or formal proof."""
from dataclasses import dataclass, asdict
import ctypes as C
import hashlib
import json
from benchmark import py, load, pack, invoke, ROOT
from round3 import Prepared, prepare
from sparse import propagate, BudgetExceeded

SCOPE="Exact signed Pauli conjugation U^dagger post U = pre; admitted gate alphabet only; global circuit phase irrelevant"
def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def valid_pauli(p,n):
    if type(p) is not tuple or len(p)!=3 or any(type(x) is not int for x in p) or not 0<=p[0]<1<<n or not 0<=p[1]<1<<n or p[2] not in (0,1):
        raise ValueError("signed Pauli")

@dataclass(frozen=True)
class Obligation:
    pre: tuple
    post: tuple

@dataclass(frozen=True)
class Witness:
    axes: tuple
    signs: tuple
    numerator: tuple
    denominator_power: int

@dataclass(frozen=True)
class Report:
    status: str
    method: str
    circuit_id: str
    obligation_id: str
    scope: str
    reason: str
    witness: Witness|None=None
    def require(self):
        if self.status!="PASS":raise AssertionError(self.status+": "+self.reason)
        return self

def admission(pre):
    if type(pre) is not Prepared or type(pre.width) is not int or not 1<=pre.width<=64 or type(pre.gates) is not tuple or len(pre.gates)>100_000 or type(pre.packed) is not bytes or len(pre.packed)!=3*len(pre.gates):raise ValueError("prepared input")
    data=bytearray()
    for row in pre.gates:
        if type(row) is not tuple or len(row)!=3 or any(type(v) is not int for v in row):raise ValueError("gate")
        op,a,b=row
        if not 0<=op<=7 or not 0<=a<pre.width or (op==5 and (not 0<=b<pre.width or a==b)) or (op!=5 and b!=0):raise ValueError("gate")
        data.extend(row)
    if data!=pre.packed:raise ValueError("inconsistent prepared input")
    return digest({"width":pre.width,"gates":pre.gates,"scope":SCOPE})

def _add(d,key,a,b):
    u,v=d.get(key,(0,0));p=(u+a,v+b)
    if p==(0,0):d.pop(key,None)
    else:d[key]=p

def difference(terms,k,pre):
    d={(x,z):(a,b) for x,z,a,b in terms}
    _add(d,(pre[0],pre[1]),-((-1)**pre[2])*(1<<k),0)
    return d

def product_witness(n,d,k):
    """A nonzero Pauli polynomial has a nonzero product-state expectation.
    Choose local axes supporting one nonzero monomial, then condition signs
    without eliminating the nonzero polynomial. All arithmetic exact.
    """
    if not d:raise ValueError("zero difference")
    x,z=next(iter(d))
    axes=tuple("IZXY"[2*((x>>i)&1)+((z>>i)&1)] if (x|z)&(1<<i) else "Z" for i in range(n))
    ax=sum((a in "XY")<<i for i,a in enumerate(axes))
    az=sum((a in "ZY")<<i for i,a in enumerate(axes))
    poly={}
    for (x,z),(a,b) in d.items():
        mask=x|z
        if ((x^ax)|(z^az))&mask:continue
        _add(poly,mask,a,b)
    assert poly
    signs=[]
    for i in range(n):
        bit=1<<i
        def reduce(s):
            out={}
            for mask,(a,b) in poly.items():
                mul=s if mask&bit else 1
                _add(out,mask&~bit,mul*a,mul*b)
            return out
        plus=reduce(1)
        if plus:signs.append(1);poly=plus
        else:signs.append(-1);poly=reduce(-1)
        assert poly
    assert set(poly)=={0}
    return Witness(axes,tuple(signs),poly[0],k)

class Native:
    def __init__(self):
        self.scalar=load("cpp.so")
        self.dll=C.CDLL(str(ROOT/"batch.so"));self.batch=self.dll.batch_bitslice
        self.batch.argtypes=[C.POINTER(C.c_uint8),C.c_size_t,C.c_uint32,C.POINTER(C.c_uint64),C.POINTER(C.c_uint64),C.POINTER(C.c_uint8),C.c_size_t];self.batch.restype=C.c_int
    def run(self,pre,ps,method):
        buf=(C.c_uint8*len(pre.packed)).from_buffer_copy(pre.packed)
        if method=="scalar":return [invoke(self.scalar,buf,pre.width,p) for p in ps]
        m=len(ps);x=(C.c_uint64*m)(*(p[0] for p in ps));z=(C.c_uint64*m)(*(p[1] for p in ps));r=(C.c_uint8*m)(*(p[2] for p in ps))
        if self.batch(buf,len(buf)//3,pre.width,x,z,r,m):raise ValueError("native rejection")
        return list(zip(x,z,r))

def verify(pre,obligations,*,native=None,method="auto",max_terms=4096,max_work=2_000_000):
    cid=admission(pre)
    return _verify_admitted(pre,cid,any(g[0]>=6 for g in pre.gates),obligations,native=native,method=method,max_terms=max_terms,max_work=max_work)

def _verify_admitted(pre,cid,has_t,obligations,*,native=None,method="auto",max_terms=4096,max_work=2_000_000):
    # Private research helper; only call after admission of immutable Prepared.
    if type(obligations) not in (tuple,list) or not 1<=len(obligations)<=64:raise ValueError("obligation count")
    if method not in ("auto","scalar","batch","python","sparse"):raise ValueError("method")
    if type(max_terms) is not int or not 1<=max_terms<=4096 or type(max_work) is not int or not 1<=max_work<=2_000_000:raise ValueError("budget")
    for ob in obligations:
        if type(ob) is not Obligation:raise TypeError("obligation")
        valid_pauli(ob.pre,pre.width);valid_pauli(ob.post,pre.width)
    if method=="auto":
        method="sparse" if has_t else ("batch" if native is not None and len(obligations)>=8 else "scalar" if native is not None else "python")
    def report(ob,status,reason,w=None):
        return Report(status,method,cid,digest(asdict(ob)),SCOPE,reason,w)
    if (has_t and method!="sparse") or (method in ("scalar","batch") and native is None):
        return tuple(report(o,"UNSUPPORTED","method not admitted") for o in obligations)
    # Total term-work/Clifford gate visits are bounded for the request.
    if method!="sparse":
        if len(pre.gates)*len(obligations)>max_work:
            return tuple(report(o,"INCONCLUSIVE","work cap") for o in obligations)
        ps=[o.post for o in obligations]
        values=[py(pre.gates,pre.width,p) for p in ps] if method=="python" else native.run(pre,ps,method)
        outputs=[(((x,z,(-1)**r,0),),0) for x,z,r in values]
    else:
        outputs=[];remaining=max_work
        for ob in obligations:
            if remaining<=0:outputs.append(None);continue
            try:
                r=propagate(pre.width,pre.gates,ob.post,max_terms=max_terms,max_work=remaining)
            except BudgetExceeded:
                outputs.append(None)
                remaining=0 # conservatively consume remaining budget on abort
            else:
                remaining-=r.work;outputs.append((r.terms,r.denominator_power))
    result=[]
    for ob,out in zip(obligations,outputs):
        if out is None:result.append(report(ob,"INCONCLUSIVE","term/work budget"));continue
        terms,k=out;d=difference(terms,k,ob.pre)
        if not d:result.append(report(ob,"PASS","exact coefficient equality"))
        else:result.append(report(ob,"FAIL","nonzero exact product-state expectation",product_witness(pre.width,d,k)))
    return tuple(result)

def compose(first,second,initial,middle,final,*,native=None,max_work=2_000_000):
    """If local identities hold, transitivity proves the composed identity.
    A local failure does not imply global failure. Return local evidence and
    a distinct direct result (or budget-inconclusive); never reuse stale reports.
    """
    admission(first);admission(second)
    if first.width!=second.width or len(first.gates)+len(second.gates)>100_000:raise ValueError("composition bounds")
    if type(max_work) is not int or not 1<=max_work<=2_000_000:raise ValueError("budget")
    local_budget=max_work//3
    if local_budget==0:raise ValueError("composition budget")
    a=verify(first,(Obligation(initial,middle),),native=native,max_work=local_budget)[0]
    b=verify(second,(Obligation(middle,final),),native=native,max_work=local_budget)[0]
    ob=Obligation(initial,final)
    joined=Prepared(first.width,first.gates+second.gates,first.packed+second.packed)
    cid=admission(joined)
    if a.status==b.status=="PASS":
        r=Report("PASS","composition",cid,digest(asdict(ob)),SCOPE,"two exact local identities and matching middle Pauli")
    else:r=verify(joined,(ob,),native=native,max_work=local_budget)[0]
    return (a,b),r
