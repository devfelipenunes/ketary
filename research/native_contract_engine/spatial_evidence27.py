"""Portable spatial replay record. Independent mathematical replay is required.
Not a succinct proof, signature, or certificate of execution time.
"""
import hashlib,json
from dataclasses import dataclass
from independent20 import pauli
from planner19 import snapshot_id
from spatial26 import verify as spatial

MAX=16384
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode("ascii")
def digest_terms(terms):
    return hashlib.sha256(canonical([[x,z,[[a.numerator,a.denominator] for a in c]] for (x,z),c in terms])).hexdigest()
def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError("duplicate")
        d[k]=v
    return d
def integer(s):
    if len(s)>21:raise ValueError("integer")
    return int(s)
def bad(s):raise ValueError("number")
@dataclass(frozen=True)
class Receipt:
    status:str
    witness:object
    record:bytes|None
    ledger:object

def produce(n,g,pre,post,partition,*,max_work=2_000_000,max_terms=4096,max_bits=512):
    r=spatial(n,g,pre,post,partition,max_work=max_work,max_terms=max_terms,max_bits=max_bits)
    if r.status=="INCONCLUSIVE":return Receipt(r.status,None,None,r.ledger)
    b={"v":1,"kind":"spatial-pauli-replay","width":n,"snapshot":r.circuit_id,
       "pre":pre,"post":post,"partition":partition,"status":r.status,
       "max_terms":max_terms,"max_bits":max_bits,"result":digest_terms(r.terms)}
    raw=canonical({"body":b,"sha256":hashlib.sha256(canonical(b)).hexdigest()})
    if len(raw)>MAX:raise ValueError("record size")
    return Receipt(r.status,r.witness,raw,r.ledger)

def replay(n,g,pre,post,raw,*,max_work=2_000_000):
    # Caller owns replay budget; record cannot increase it.
    pauli(n,pre);pauli(n,post)
    if type(g) is not bytes or len(g)%3 or len(g)>12288 or type(max_work) is not int or not 1<=max_work<=2_000_000:raise ValueError("input")
    if type(raw) is not bytes or not 1<=len(raw)<=MAX:return None
    try:
        obj=json.loads(raw.decode("ascii"),object_pairs_hook=unique,parse_int=integer,parse_float=bad,parse_constant=bad)
        if type(obj) is not dict or set(obj)!={"body","sha256"}:return None
        b=obj["body"]
        if type(b) is not dict or set(b)!={"v","kind","width","snapshot","pre","post","partition","status","max_terms","max_bits","result"}:return None
        if raw!=canonical(obj) or obj["sha256"]!=hashlib.sha256(canonical(b)).hexdigest():return None
        if type(b["v"]) is not int or b["v"]!=1 or b["kind"]!="spatial-pauli-replay" or type(b["width"]) is not int or b["width"]!=n or b["snapshot"]!=snapshot_id(n,g):return None
        if type(b["pre"]) is not list or type(b["post"]) is not list:return None
        a=pauli(n,tuple(b["pre"]));p=pauli(n,tuple(b["post"]))
        if (a,p)!=(pre,post) or b["status"] not in ("PASS","FAIL"):return None
        if type(b["partition"]) is not list or any(type(w) is not list for w in b["partition"]):return None
        part=tuple(tuple(w) for w in b["partition"])
        r=spatial(n,g,pre,post,part,max_work=max_work,max_terms=b["max_terms"],max_bits=b["max_bits"])
        if r.status!=b["status"] or digest_terms(r.terms)!=b["result"]:return None
        return r
    except (ValueError,TypeError,KeyError,OverflowError,RecursionError,UnicodeError):return None
