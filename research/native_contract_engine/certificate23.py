"""Bounded portable JSON certificate envelope. Integrity is not authenticity.
Verifier replays local mathematics; no Rust result is trusted.
"""
import hashlib,json
from cuts21 import Certificate,Segment,check_certificate
from engine import valid_pauli
from native9 import bounds

MAX_BYTES=1_048_576

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")

def body(cert):
    return {"version":1,"kind":"signed-pauli-temporal","circuit_id":cert.circuit_id,
            "width":cert.width,"pre":cert.pre,"post":cert.post,
            "segments":[[s.start,s.end,s.pre,s.post] for s in cert.segments]}

def encode(cert):
    if type(cert) is not Certificate:raise TypeError("certificate")
    b=body(cert);raw=canonical({"body":b,"sha256":hashlib.sha256(canonical(b)).hexdigest()})
    if len(raw)>MAX_BYTES:raise ValueError("certificate byte cap")
    return raw

def unique(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError("duplicate key")
        out[k]=v
    return out

def integer(s):
    if len(s)>21:raise ValueError("integer cap")
    return int(s)

def reject_number(s):raise ValueError("integer-only schema")

def decode(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=MAX_BYTES:raise ValueError("certificate size")
    try:
        obj=json.loads(raw.decode("ascii"),object_pairs_hook=unique,parse_int=integer,
                       parse_float=reject_number,parse_constant=reject_number)
        if type(obj) is not dict or set(obj)!={"body","sha256"}:raise ValueError("envelope")
        b=obj["body"]
        if type(b) is not dict or set(b)!={"version","kind","circuit_id","width","pre","post","segments"}:raise ValueError("body")
        if type(b["version"]) is not int or b["version"]!=1 or b["kind"]!="signed-pauli-temporal":raise ValueError("version")
        digest=obj["sha256"]
        if type(digest) is not str or len(digest)!=64 or digest!=hashlib.sha256(canonical(b)).hexdigest():raise ValueError("integrity")
        if raw!=canonical(obj):raise ValueError("noncanonical encoding")
        n=b["width"];cid=b["circuit_id"]
        if type(n) is not int or not 1<=n<=64 or type(cid) is not str or len(cid)!=64 or any(c not in "0123456789abcdef" for c in cid):raise ValueError("snapshot")
        def p(a):
            if type(a) is not list or len(a)!=3:raise ValueError("pauli")
            a=tuple(a);valid_pauli(a,n);return a
        pre,post=p(b["pre"]),p(b["post"])
        rows=b["segments"]
        if type(rows) is not list or len(rows)>4096:raise ValueError("segments")
        out=[]
        for s in rows:
            if type(s) is not list or len(s)!=4:raise ValueError("segment")
            a,z,x,y=s
            if type(a) is not int or type(z) is not int or not 0<=a<z<=4096 or z-a>32:raise ValueError("range")
            out.append(Segment(a,z,p(x),p(y)))
        return Certificate(cid,n,pre,post,tuple(out))
    except (RecursionError,UnicodeError,TypeError,KeyError,OverflowError) as e:
        raise ValueError("malformed certificate") from e

def verify_bytes(n,g,pre,post,raw,*,max_work=2_000_000):
    bounds(4096,max_work)
    try:c=decode(raw)
    except ValueError:return False
    return check_certificate(n,g,pre,post,c,max_work=max_work)
