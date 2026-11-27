"""Research: strict evidence schema, version and implementation fingerprints."""
import hashlib,json,pathlib
from common5 import *
from dataclasses import asdict
import importlib.metadata as md
from engine import SCOPE
ROOT=pathlib.Path(__file__).resolve().parent
def fingerprint():
    return {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ("engine.py","sparse.py","benchmark.py","round3.py","front_e6.py")}
def make(p,ob,*,max_terms=4096,max_work=2_000_000):
    r=verify(p,(ob,),method="sparse",max_terms=max_terms,max_work=max_work)[0]
    payload={"schema":2,"scope":SCOPE,"versions":{"ketary":md.version("ketary"),"qiskit":md.version("qiskit")},"implementation":fingerprint(),"budget":{"max_terms":max_terms,"max_work":max_work},"obligation":asdict(ob),"report":asdict(r)}
    return json.dumps({"payload":payload,"sha256":digest(payload)},sort_keys=True,separators=(",",":"))
def strict(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError("duplicate key")
        d[k]=v
    return d
def replay(p,ob,raw,*,max_terms=4096,max_work=2_000_000):
    if type(raw) is not str or len(raw)>32768:raise ValueError("size")
    data=json.loads(raw,object_pairs_hook=strict,parse_constant=lambda _:(_ for _ in ()).throw(ValueError("constant")))
    expected=json.loads(make(p,ob,max_terms=max_terms,max_work=max_work))
    if json.dumps(data,sort_keys=True,separators=(",",":"))!=json.dumps(expected,sort_keys=True,separators=(",",":")):raise ValueError("mismatch")
    return data["payload"]["report"]["status"]
def main():
    count=reject=0
    for n in (2,5,16,32):
        p=prepare(circuit(n,[(6,0,0)]),allow_t=True)
        for ob in (Obligation((0,1,0),(0,1,0)),Obligation((1,0,0),(1,0,0))):
            raw=make(p,ob);assert replay(p,ob,raw)==verify(p,(ob,))[0].status;count+=1
            obj=json.loads(raw)
            for field,value in (("schema",True),("scope","false"),("budget",{"max_terms":1,"max_work":1}),("implementation",{}),("versions",{})):
                mod=json.loads(raw);mod["payload"][field]=value;mod["sha256"]=digest(mod["payload"])
                try:replay(p,ob,json.dumps(mod))
                except ValueError:reject+=1
                else:raise AssertionError("tamper")
            for invalid in ('{"payload":{},"payload":{},"sha256":"x"}','{"payload":NaN,"sha256":"x"}'):
                try:replay(p,ob,invalid)
                except ValueError:reject+=1
                else:raise AssertionError("invalid JSON")
    output({"scope":"strict deterministic replay with source fingerprints; hash is not authentication or independent proof","replays":count,"rejections":reject})
if __name__=="__main__":main()
