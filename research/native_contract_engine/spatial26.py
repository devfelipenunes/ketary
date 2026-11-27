"""Independent spatial-block Pauli transfer via exact basis columns.

Partition wires into blocks of at most 3. Cross-block CX is a separate
two-wire transfer; within each epoch disjoint block gates commute.
Every local transfer uses exact state-column arithmetic, not native
propagation. Global sparse expansion may still be exponential.
"""
from dataclasses import dataclass
from independent20 import column,action,add,pauli,ZERO
from expectation23 import cmul,conjugate
from engine import product_witness
from planner19 import snapshot_id
from fractions import Fraction

@dataclass(frozen=True)
class Ledger:
    reserved:int
    used:int
    peak_terms:int
    max_bits:int
    transfers:int
    crossings:int

@dataclass(frozen=True)
class Result:
    status:str
    circuit_id:str
    ledger:Ledger
    witness:object=None
    terms:tuple=()

class Limit(Exception):pass

def mul(a,b):return a[0]*b[0]+2*a[1]*b[1],a[0]*b[1]+a[1]*b[0]

def verify(n,g,pre,post,partition,*,max_work=2_000_000,max_terms=4096,max_bits=512):
    if type(n) is not int or not 1<=n<=64 or type(g) is not bytes or len(g)%3 or len(g)>12288:raise ValueError("snapshot")
    if type(max_work) is not int or not 1<=max_work<=2_000_000 or type(max_terms) is not int or not 1<=max_terms<=4096 or type(max_bits) is not int or not 1<=max_bits<=512:raise ValueError("budget")
    pauli(n,pre);pauli(n,post)
    if type(partition) is not tuple or not 1<=len(partition)<=64 or any(type(w) is not tuple or not 1<=len(w)<=3 or any(type(i) is not int for i in w) for w in partition):raise ValueError("partition")
    if sorted(i for w in partition for i in w)!=list(range(n)):raise ValueError("partition coverage")
    owner={w:j for j,ws in enumerate(partition) for w in ws}
    maps=[{w:j for j,w in enumerate(ws)} for ws in partition]
    rows=tuple(zip(g[::3],g[1::3],g[2::3]))
    for op,a,b in rows:
        if op>7 or a>=n or (op==5 and (b>=n or a==b)) or (op!=5 and b!=0):raise ValueError("gate")
    used=0;peak=1;bits=1;cross=0;transfers=0;cache={}
    cid=snapshot_id(n,g)
    def charge(k):
        nonlocal used
        if used+k>max_work:raise Limit()
        used+=k
    def coefficient(a):
        nonlocal bits
        b=max((abs(c.numerator).bit_length()+c.denominator.bit_length() for c in a),default=0)
        bits=max(bits,b)
        if b>max_bits:raise Limit()
        return a
    def local(w,packed,p):
        nonlocal transfers
        charge(1);key=w,packed,p
        if key in cache:return cache[key]
        d=1<<w;r=tuple(zip(packed[::3],packed[1::3],packed[2::3]))
        # Conservative visits including all Pauli-basis traces.
        charge(d*d*(len(r)+4)+d**4*4)
        cols=[column(w,r,j) for j in range(d)]
        k=cols[0][1];den=1<<(2*k+w)
        # <i| U† P U |j> = <U i|P U j>.
        acted=[action(v,p) for v,_ in cols]
        out=[]
        for x in range(d):
            for z in range(d):
                total=ZERO
                for j in range(d):
                    v=cols[j^x][0];a=acted[j]
                    inner=ZERO
                    for s,t in zip(v,a):inner=add(inner,cmul(conjugate(s),t))
                    # Tr(Q O): Q_{j,j xor x}=conj(Q_{j xor x,j}).
                    from independent20 import iphase
                    phase=-((x&z).bit_count()+2*((j&z).bit_count()%2))
                    total=add(total,iphase(inner,phase))
                if total[2:]!=(0,0):raise ArithmeticError("Hermitian transfer")
                co=coefficient((Fraction(total[0],den),Fraction(total[1],den)))
                if co!=(0,0):out.append((x,z,co))
        transfers+=1;cache[key]=tuple(out);return cache[key]
    poly={post[:2]:(Fraction((-1)**post[2]),Fraction(0))}
    def apply(ws,packed):
        nonlocal poly,peak
        mask=sum(1<<w for w in ws);out={}
        def sub(v):return sum(((v>>w)&1)<<i for i,w in enumerate(ws))
        def lift(v):return sum(((v>>i)&1)<<w for i,w in enumerate(ws))
        for (x,z),c in poly.items():
            for u,v,t in local(len(ws),packed,(sub(x),sub(z),0)):
                charge(1+len(ws))
                key=(x&~mask|lift(u),z&~mask|lift(v))
                a,b=out.get(key,(0,0));d,e=mul(c,t);co=coefficient((a+d,b+e))
                if co==(0,0):out.pop(key,None)
                else:out[key]=co
                if len(out)>max_terms:raise Limit()
                peak=max(peak,len(out))
        poly=out
    def flush(blocks):
        for j,buf in enumerate(blocks):
            if buf:apply(partition[j],bytes(buf))
    try:
        charge(len(g)+n)
        # Reverse epochs, maintaining original gate order inside each local block.
        blocks=[bytearray() for _ in partition]
        for op,a,b in reversed(rows):
            j=owner[a]
            if op==5 and j!=owner[b]:
                flush(blocks);blocks=[bytearray() for _ in partition]
                apply((a,b),bytes((5,0,1)));cross+=1
            else:
                m=maps[j];blocks[j][:0]=bytes((op,m[a],m[b] if op==5 else 0))
                if len(blocks[j])//3>=32:
                    # Flush all blocks; no cross gates within epoch.
                    flush(blocks);blocks=[bytearray() for _ in partition]
        flush(blocks)
        charge(len(poly)+1)
        delta=poly.copy();a,b=delta.get(pre[:2],(0,0));v=(a-(-1)**pre[2],b)
        if v==(0,0):delta.pop(pre[:2],None)
        else:delta[pre[:2]]=v
        w=None
        if delta:
            charge((2*n+3)*len(delta))
            k=max(c.denominator.bit_length()-1 for t in delta.values() for c in t)
            d={p:tuple(int(c*(1<<k)) for c in t) for p,t in sorted(delta.items())}
            w=product_witness(n,d,k)
        return Result("FAIL" if delta else "PASS",cid,Ledger(max_work,used,peak,bits,transfers,cross),w,tuple(sorted(poly.items())))
    except Limit:return Result("INCONCLUSIVE",cid,Ledger(max_work,used,peak,bits,transfers,cross))
