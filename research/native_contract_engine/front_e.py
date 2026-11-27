"""E: versioned evidence, canonical serialization and independent replay."""
from common5 import *
from dataclasses import asdict
import importlib.metadata as md
from engine import SCOPE

VERSION="pauli-transition-research-v1"
def evidence(pre,ob):
    r=verify(pre,(ob,))[0]
    if r.status not in ("PASS","FAIL"):raise ValueError("only decided evidence")
    payload={"schema":1,"engine":VERSION,"ketary":md.version("ketary"),"qiskit":md.version("qiskit"),"scope":SCOPE,"obligation":asdict(ob),"report":asdict(r)}
    return json.dumps({"payload":payload,"sha256":digest(payload)},sort_keys=True,separators=(",",":"))

def replay(pre,ob,raw):
    if type(raw) is not str or len(raw)>32768:raise ValueError("evidence size")
    data=json.loads(raw)
    if type(data) is not dict or set(data)!={"payload","sha256"}:raise ValueError("schema")
    if digest(data["payload"])!=data["sha256"]:raise ValueError("integrity")
    # Re-evaluate against independently supplied obligation and prepared snapshot;
    # even an attacker recomputing the hash cannot substitute a false verdict.
    expected=json.loads(evidence(pre,ob))
    if data!=expected:raise ValueError("stale, incompatible or inconsistent evidence")
    return data["payload"]["report"]["status"]

def main():
    rng=random.Random(11);checks=0;reject=0
    for n in (2,3,4,5,16,32):
        for j in range(8):
            p=prepare(circuit(n,gates(n,25,j)))
            ob=Obligation((rng.getrandbits(n),rng.getrandbits(n),0),(rng.getrandbits(n),rng.getrandbits(n),0))
            raw=evidence(p,ob);assert replay(p,ob,raw)==verify(p,(ob,))[0].status;checks+=1
            for field,value in (("engine","wrong"),("scope","all programs"),("qiskit","wrong")):
                obj=json.loads(raw);obj["payload"][field]=value;obj["sha256"]=digest(obj["payload"])
                try:replay(p,ob,json.dumps(obj))
                except ValueError:reject+=1
                else:raise AssertionError("forgery")
            obj=json.loads(raw);rr=obj["payload"]["report"];rr["status"]="PASS" if rr["status"]=="FAIL" else "FAIL";obj["sha256"]=digest(obj["payload"])
            try:replay(p,ob,json.dumps(obj))
            except ValueError:reject+=1
            else:raise AssertionError("forged report")
            altered=prepare(circuit(n,list(p.gates)+[(3,0,0)]))
            try:replay(altered,ob,raw)
            except ValueError:reject+=1
            else:raise AssertionError("stale input")
    output({"scope":"version-bound deterministic re-evaluation; hash not authentication; independent numerical witness validation remains separate","replays":checks,"rejections":reject})
if __name__=="__main__":main()
