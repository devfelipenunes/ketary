"""Compact canonical binary temporal certificate. No authentication claim.

Store each boundary only once, with width-dependent masks and one byte
segment length. Original snapshot identity and independent replay retained.
"""
import hashlib
from cuts21 import Certificate,Segment,check_certificate
from engine import valid_pauli
from native9 import bounds
MAGIC=b"KTCB\x01"
MAX=100000

def encode(c):
    if type(c) is not Certificate or type(c.width) is not int or not 1<=c.width<=64:raise ValueError("certificate")
    n=c.width;w=(n+7)//8
    if type(c.circuit_id) is not str or len(c.circuit_id)!=64 or any(x not in "0123456789abcdef" for x in c.circuit_id):raise ValueError("identity")
    if type(c.segments) is not tuple or len(c.segments)>4096:raise ValueError("segments")
    def p(x):
        valid_pauli(x,n);return x[0].to_bytes(w,"big")+x[1].to_bytes(w,"big")+bytes([x[2]])
    raw=bytearray(MAGIC+bytes([n])+bytes.fromhex(c.circuit_id)+len(c.segments).to_bytes(2,"big")+p(c.pre))
    end=0;prev=c.pre
    for s in c.segments:
        if type(s) is not Segment or type(s.start) is not int or type(s.end) is not int or s.start!=end or not end<s.end<=4096 or s.end-end>32 or s.pre!=prev:raise ValueError("segment chain")
        raw.extend(bytes([s.end-end])+p(s.post));end=s.end;prev=s.post
    valid_pauli(c.post,n)
    if prev!=c.post:raise ValueError("endpoint")
    raw.extend(hashlib.sha256(raw).digest())
    if len(raw)>MAX:raise ValueError("size")
    return bytes(raw)

def decode(raw):
    if type(raw) is not bytes or not 75<=len(raw)<=MAX or raw[:5]!=MAGIC:raise ValueError("envelope")
    n=raw[5]
    if not 1<=n<=64:raise ValueError("width")
    w=(n+7)//8;size=2*w+1;count=int.from_bytes(raw[38:40],"big")
    if count>4096 or len(raw)!=40+size+count*(1+size)+32:raise ValueError("size")
    if hashlib.sha256(raw[:-32]).digest()!=raw[-32:]:raise ValueError("integrity")
    i=40
    def p():
        nonlocal i
        a=(int.from_bytes(raw[i:i+w],"big"),int.from_bytes(raw[i+w:i+2*w],"big"),raw[i+2*w]);i+=size
        valid_pauli(a,n);return a
    pre=p();prev=pre;end=0;rows=[]
    for _ in range(count):
        k=raw[i];i+=1
        if not 1<=k<=32 or end+k>4096:raise ValueError("segment")
        post=p();rows.append(Segment(end,end+k,prev,post));end+=k;prev=post
    return Certificate(raw[6:38].hex(),n,pre,prev,tuple(rows))

def verify(n,g,pre,post,raw,*,max_work=2_000_000):
    bounds(4096,max_work)
    try:c=decode(raw)
    except ValueError:return False
    return check_certificate(n,g,pre,post,c,max_work=max_work)
