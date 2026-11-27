"""R21 bounded temporal cuts and replayable Pauli boundary certificates.
No arbitrary spatial circuit cutting or succinct proof claim."""
from dataclasses import dataclass
from native9 import RustSession,bounds,reduce_cone
from engine import valid_pauli
from sparse import BudgetExceeded
from independent20 import verify_transition
from planner19 import independent_verdict,plan_transition,snapshot_id

@dataclass(frozen=True)
class Segment:
    start:int
    end:int
    pre:tuple
    post:tuple

@dataclass(frozen=True)
class Certificate:
    circuit_id:str
    width:int
    pre:tuple
    post:tuple
    segments:tuple

def cuts(session,pre,post,*,chunk=16,max_work=2_000_000):
    """Derive intermediate signed Paulis backwards. Non-Pauli boundaries
    are inconclusive; each exact local identity composes."""
    if type(session) is not RustSession or type(chunk) is not int or not 1<=chunk<=32:raise ValueError("input")
    bounds(4096,max_work);n=session.width;g=session.packed
    valid_pauli(pre,n);valid_pauli(post,n)
    if len(g)//3>4096:return None
    rem=max_work-len(g);p=post;out=[]
    if rem<=0:return None
    end=len(g)//3
    while end:
        start=max(0,end-chunk);local=g[3*start:3*end]
        rem-=len(local)+1
        if rem<=0:return None
        try:r=RustSession(n,local).propagate(p,max_work=rem)
        except BudgetExceeded:return None
        rem-=r.work+len(r.terms)
        if rem<0 or len(r.terms)!=1:return None
        x,z,a,b=r.terms[0]
        if b or abs(a)!=1<<r.denominator_power:return None
        q=x,z,int(a<0);out.append(Segment(start,end,q,p));p=q;end=start
    if p!=pre:return None
    return Certificate(session.identity,n,pre,post,tuple(reversed(out)))

def check_certificate(n,g,pre,post,cert,*,max_work=2_000_000):
    """Independent local replay, bound to caller request and entire snapshot.
    A missing certificate is inconclusive, not evidence of failure."""
    bounds(4096,max_work);valid_pauli(pre,n);valid_pauli(post,n)
    if type(g) is not bytes or len(g)%3 or len(g)>12288:raise ValueError("snapshot")
    if type(cert) is not Certificate or (cert.width,cert.circuit_id,cert.pre,cert.post)!=(n,snapshot_id(n,g),pre,post):return False
    if type(cert.segments) is not tuple or len(cert.segments)>4096:return False
    rem=max_work-len(g);end=0;p=pre
    for s in cert.segments:
        if type(s) is not Segment or type(s.start) is not int or type(s.end) is not int or s.start!=end or not end<s.end<=len(g)//3 or s.end-end>32 or s.pre!=p:return False
        valid_pauli(s.pre,n);valid_pauli(s.post,n)
        local=g[3*end:3*s.end];count=s.end-end
        if any(op>=6 for op in local[::3]):
            # Restrict exact columns to the actual local support; Pauli
            # outside support must agree (sign is assigned to active part).
            active=sorted({w for op,a,b in zip(local[::3],local[1::3],local[2::3]) for w in ((a,b) if op==5 else (a,))})
            if not active or len(active)>5:return False
            mask=sum(1<<i for i in active)
            if any((s.pre[j]^s.post[j])&~mask for j in (0,1)):return False
            m={w:i for i,w in enumerate(active)}
            packed=bytes(v for op,a,b in zip(local[::3],local[1::3],local[2::3]) for v in (op,m[a],m[b] if op==5 else 0))
            def sub(q):return tuple(sum(((q[j]>>w)&1)<<i for i,w in enumerate(active)) for j in (0,1))+(q[2],)
            cost=(1<<(2*len(active)))*(count+4)
            if cost>rem:return False
            good=verify_transition(len(active),packed,sub(s.pre),sub(s.post),max_work=cost).status=="PASS"
        else:
            cost=max(1,(2*n+2)*count)
            if cost>rem:return False
            good=independent_verdict(n,local,s.pre,s.post,max_work=cost)=="PASS"
        if not good:return False
        rem-=cost;end=s.end;p=s.post
    return rem>=0 and end==len(g)//3 and p==post

def adaptive(session,pre,post,*,max_terms=4096,max_work=2_000_000):
    """Preselect cone for T-rich snapshots, then use bounded old planner.
    Return provenance; no timing-based semantic changes."""
    bounds(max_terms,max_work);valid_pauli(pre,session.width);valid_pauli(post,session.width)
    g=session.packed;scan=len(g)
    if scan<max_work//4 and sum(op>=6 for op in g[::3])>32:
        reduced=reduce_cone(g,post)
        if len(reduced)<len(g)//2:
            r=plan_transition(RustSession(session.width,reduced),pre,post,max_terms=max_terms,max_work=max_work-scan)
            if r.status!="INCONCLUSIVE":return ("preselected-cone",r.status,session.identity,r)
            return ("preselected-cone","INCONCLUSIVE",session.identity,r)
    r=plan_transition(session,pre,post,max_terms=max_terms,max_work=max_work)
    return ("baseline",r.status,session.identity,r)
