"""R23 validation of prepared routing, portable certificates and DAG contracts."""
import json,random,sys,hashlib
from dataclasses import replace
from common5 import circuit,measure
from benchmark import label
from native9 import RustSession
from planner19 import plan_transition
from prepared23 import Prepared
from cuts21 import cuts
from certificate23 import encode,decode,verify_bytes,canonical
from dag22 import simulate
from expectation23 import expectation,eigen_contract
from independent20 import column,admit
from qiskit.quantum_info import Pauli,Operator
import numpy as np

def pack(gs):return bytes(v for g in gs for v in g)
def prepared():
    checks=0;rows=[];rng=random.Random(2301)
    for n in (2,4,8,16,32,64):
        gs=[]
        for _ in range(512):
            a,b=rng.sample(range(n),2);op=rng.randrange(6);gs.append((op,a,b if op==5 else 0))
        s=RustSession(n,pack(gs));p=Prepared(s)
        items=[]
        for i in range(32):
            b=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
            r=s.propagate(b);x,z,c,_=r.terms[0];a=(x,z,int(c<0)^(i%2));items.append((a,b))
        items=tuple(items)
        got=p.transitions(items)
        assert all(r.status==("PASS" if i%2==0 else "FAIL") and r.circuit_id==s.identity for i,r in enumerate(got))
        for r,(a,b) in zip(got,items):
            ref=plan_transition(s,a,b)
            assert r.status==ref.status and r.witness==ref.witness
            if n<=4:
                from test_engine import witness_state
                u=Operator(circuit(n,gs).to_qiskit()).data
                if r.witness:
                    v=witness_state(r.witness);d=u.conj().T@Pauli(label(n,b)).to_matrix()@u-Pauli(label(n,a)).to_matrix()
                    assert abs(np.vdot(v,d@v).real-r.witness.numerator[0])<1e-8
            checks+=1
        assert all(r.status=="INCONCLUSIVE" for r in p.transitions(items,max_work=1))
        assert Prepared(s,max_build_work=1).tableau is None
        rows.append({"n":n,"setup":measure({"prepare":lambda:Prepared(s)},reps=9),"batch32":measure({"prepared":lambda:p.transitions(items),"baseline":lambda:tuple(plan_transition(s,a,b) for a,b in items)},reps=9)})
    s=RustSession(2,pack([(6,0,0)]));p=Prepared(s)
    assert p.tableau is None and p.transitions((((0,1,0),(0,1,0)),))[0].status=="PASS"
    return {"checks":checks+13,"rows":rows,"scope":"private prepared contract reports including exact failure witness"}

def certificate():
    checks=0;rows=[]
    for n in (2,8,16,32,64):
        gs=[g for i in range(n) for g in [(6,i,0),(4,i,0),(7,i,0),(4,i,0)]]
        g=pack(gs);s=RustSession(n,g);p=((1<<n)-1,0,0)
        cert=cuts(s,p,p,chunk=4);assert cert
        raw=encode(cert);assert decode(raw)==cert and verify_bytes(n,g,p,p,raw)
        # An attacker may recompute the digest; independent replay must still reject.
        obj=json.loads(raw)
        obj["body"]["segments"][0][3][2]^=1
        obj["sha256"]=hashlib.sha256(canonical(obj["body"])).hexdigest()
        assert not verify_bytes(n,g,p,p,canonical(obj))
        assert not verify_bytes(n,g,p,p,raw+b" ")
        assert not verify_bytes(n,g+b"\x04\x00\x00",p,p,raw)
        assert not verify_bytes(n,g,p,p,raw,max_work=1)
        assert not verify_bytes(n,g,p,p,b'{"body":{},"body":{},"sha256":"x"}')
        assert not verify_bytes(n,g,p,p,b"["*2000+b"]"*2000)
        assert not verify_bytes(n,g,p,p,b"x"*1048577)
        rows.append({"n":n,"bytes":len(raw),"segments":len(cert.segments),"timings":measure({"encode":lambda:encode(cert),"verify":lambda:verify_bytes(n,g,p,p,raw)},reps=9)})
        checks+=9
    return {"checks":checks,"rows":rows,"scope":"canonical portable JSON, independently replayed, no signature/authentication"}

def dag():
    checks=0;rows=[];rng=random.Random(2303)
    for n in (2,3,4,5):
        for j in range(16):
            gs=[]
            for _ in range(18):
                a,b=rng.sample(range(n),2);op=rng.randrange(8);gs.append((op,a,b if op==5 else 0))
            g=pack(gs);d=simulate(n,g);assert d is not None
            u=Operator(circuit(n,gs).to_qiskit()).data[:,0]
            for _ in range(12):
                p=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
                r=expectation(d,p);assert r.status=="EXACT"
                a,b=r.numerator;value=(a+b*np.sqrt(2))/(1<<r.denominator_power)
                want=np.vdot(u,Pauli(label(n,p)).to_matrix()@u).real
                assert abs(value-want)<1e-9
                assert eigen_contract(d,p)==("PASS" if abs(want-1)<1e-9 else "FAIL")
                checks+=1
    for n in (8,12,16,20):
        mask=(1<<n)-1
        g=pack([(0,0,0)]+[(5,0,i) for i in range(1,n)])
        d=simulate(n,g);assert d is not None
        for p,ok in (((mask,0,0),True),((0,3,0),True),((0,1,0),False),((mask,0,1),False)):
            assert eigen_contract(d,p)==("PASS" if ok else "FAIL");checks+=1
        r=expectation(d,(mask,0,0))
        assert expectation(d,(mask,0,0),max_work=1).status=="INCONCLUSIVE"
        rows.append({"n":n,"active_nodes":d.live_nodes(),"visits":r.visits,"timings":measure({"global_x":lambda:expectation(d,(mask,0,0))},reps=15)})
        checks+=1
    return {"checks":checks,"rows":rows,"scope":"exact pure zero-input Pauli expectations and stabilizer eigencontracts; not arbitrary unitary verification"}
if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"prepared":prepared,"certificate":certificate,"dag":dag}[sys.argv[1]]()},indent=2,allow_nan=False))
