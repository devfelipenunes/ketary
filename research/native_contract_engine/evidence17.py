"""Bounded same-engine replay records. Hashes are integrity, not authenticity."""
from dataclasses import asdict
import hashlib,json,sys
from pathlib import Path
from importlib.metadata import distribution,version
from facade17 import verify

MAX=65536
def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)
def sha(b):return hashlib.sha256(b).hexdigest()
def fingerprint():
    root=Path(__file__).resolve().parent
    names=("facade17.py","evidence17.py","engine.py","native9.py","consolidated12.py","contracts15.py","monomial16.py","contract_forms11.py","logical14.py","round3.py")
    d=distribution("ketary-native-research")
    binaries=[p for p in (d.files or ()) if str(p).endswith((".so",".pyd",".dylib"))]
    if not binaries:raise RuntimeError("installed native binary required")
    return {"python":sys.version.split()[0],"qiskit":version("qiskit"),"ketary":version("ketary"),"native_version":d.version,
            "sources":{p:sha((root/p).read_bytes()) for p in names},
            "binaries":{str(p):sha(d.locate_file(p).read_bytes()) for p in sorted(binaries,key=str)}}

def record(engine,contract,*,reference=None,policy):
    spec=contract.canonical(engine.session.width)
    r=verify(engine,contract,reference=reference,policy=policy)
    body={"schema":1,"scope":"same engine deterministic replay; not independent proof or authenticity","environment":fingerprint(),"circuit_ids":[engine.session.identity]+([] if reference is None else [reference.session.identity]),"contract":spec,"policy":asdict(policy),"report_type":type(r).__name__,"report":asdict(r)}
    out=canonical({"body":body,"digest":sha(canonical(body).encode("ascii"))}).encode("ascii")
    if len(out)>MAX:raise ValueError("evidence size")
    return out

def unique(pairs):
    o={}
    for k,v in pairs:
        if k in o:raise ValueError("duplicate key")
        o[k]=v
    return o
def bad_constant(x):raise ValueError("nonfinite JSON")
def replay(raw,engine,contract,*,reference=None,policy):
    if type(raw) is not bytes or not 1<=len(raw)<=MAX:raise ValueError("evidence bytes")
    try:d=json.loads(raw,object_pairs_hook=unique,parse_constant=bad_constant)
    except (UnicodeError,RecursionError,TypeError,ValueError) as e:raise ValueError("invalid evidence") from e
    if type(d) is not dict or set(d)!={"body","digest"} or type(d["body"]) is not dict or type(d["digest"]) is not str:raise ValueError("envelope")
    try:encoded=canonical(d).encode("ascii");digest=sha(canonical(d["body"]).encode("ascii"))
    except (ValueError,RecursionError) as e:raise ValueError("encoding") from e
    if encoded!=raw or digest!=d["digest"]:raise ValueError("canonical digest mismatch")
    # No executable data or file path taken from JSON. Caller supplies trusted
    # snapshots and typed spec. Compare full deterministic record, not PASS alone.
    if record(engine,contract,reference=reference,policy=policy)!=raw:raise ValueError("request/environment/report mismatch")
    return True
