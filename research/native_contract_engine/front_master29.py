"""R29 strict FFI admission and exact state fallback qualification."""
import json,random,sys
import numpy as np
from qiskit.quantum_info import Pauli,Statevector
from benchmark import label
from common5 import circuit,measure
from native9 import RustSession
from candidate28 import Engine,Policy,StateEigen,replay_report
from state29 import verify
from front_master28 import graph,pack
import ketary_native_research as rn

def ffi():
    calls=[]
    class Index:
        def __index__(self):calls.append("index");return 0
        def __bool__(self):calls.append("bool");return False
        def __iter__(self):calls.append("iter");return iter((0,0,0))
    class Int(int):pass
    class Tuple(tuple):pass
    class Bytes(bytes):pass
    s=rn.PackedCircuit(2,b"");t=rn.CliffordTableau(s,2_000_000)
    p=(0,0,0);pair=(p,p);items=(pair,);ps=(p,)
    checks=0
    def reject(f):
        nonlocal checks
        try:f()
        except (ValueError,TypeError,OverflowError):checks+=1;return
        raise AssertionError("malformed primitive accepted")
    for bad in (True,Int(0),Index(),-1,1<<64,1.0):
        reject(lambda:s.propagate((bad,0,0),4096,100))
        reject(lambda:s.transition((0,bad,0),p,4096,100))
        reject(lambda:t.image((0,0,bad)))
        reject(lambda:t.contracts((((bad,0,0),p),),100))
        reject(lambda:t.images(((0,bad,0),),1,100))
        reject(lambda:s.clifford_images_128(((0,bad,0),),False,100))
        reject(lambda:s.transition_batch((((bad,0,0),p),),4096,100,False))
        reject(lambda:s.projected((((0,0,bad),p),),1,4096,100,False))
    for bad in (list(p),Tuple(p),Index(),(0,0),(0,0,0,0)):
        reject(lambda:t.image(bad));reject(lambda:s.propagate(bad,4096,100))
    for bad in (True,Int(1),Index(),0,-1,2_000_001):
        reject(lambda:s.propagate(p,4096,bad))
        reject(lambda:s.transition(p,p,4096,bad))
        reject(lambda:s.transition_batch(items,4096,bad,False))
        reject(lambda:s.projected(items,1,4096,bad,False))
        reject(lambda:s.monomial_action(s,1,bad))
        reject(lambda:t.contracts(items,bad))
    for bad in (1,0,Index(),Int(1),None):
        reject(lambda:s.transition_batch(items,4096,100,bad))
        reject(lambda:s.projected(items,1,4096,100,bad))
        reject(lambda:s.clifford_images_128(ps,bad,100))
    for bad in (True,Int(2),Index(),0,65):
        reject(lambda:rn.PackedCircuit(bad,b""))
    reject(lambda:rn.PackedCircuit(2,Bytes(b"")))
    for bad in (Tuple(items),((list(p),p),), (Tuple(pair),), [pair], (pair,)*65):
        reject(lambda:s.transition_batch(bad,4096,100,False));reject(lambda:t.contracts(bad,100))
    reject(lambda:t.images(Tuple(ps),1,100))
    reject(lambda:s.clifford_images_128(Tuple(ps),True,100))
    assert not calls
    assert t.image(p)==p and t.contracts(items,100)[0][0]
    assert s.transition(p,p,4096,100)[0]
    assert s.transition_batch(items,4096,100,False)[0][0]
    return {"checks":checks+4,"scope":"strict builtin primitives, no user conversion hooks, bounded containers; not full independent unsafe-code audit"}

def fallback():
    rng=random.Random(2901);checks=0;rows=[]
    for n in (2,4,6,8):
        for j in range(12):
            gs=[]
            for _ in range(20):
                a,b=rng.sample(range(n),2);op=rng.randrange(8);gs.append((op,a,b if op==5 else 0))
            s=RustSession(n,pack(gs));dense=Statevector.from_instruction(circuit(n,gs).to_qiskit())
            e=Engine(s,Policy(state_fallback=True))
            for _ in range(8):
                p=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2));r=e.verify((StateEigen(p),)).reports[0]
                assert r.status!="INCONCLUSIVE"
                a,k=r.expectation;want=float(dense.expectation_value(Pauli(label(n,p))).real)
                assert abs((a[0]+a[1]*np.sqrt(2))/(1<<k)-want)<1e-9
                assert r.status==("PASS" if abs(want-1)<1e-9 else "FAIL")
                if n<=4:assert replay_report(s,StateEigen(p),r) is True
                checks+=1
    for n in (8,16,32,64):
        gs,obs=graph(n,2802+n);s=RustSession(n,pack(gs));i,p=obs[len(obs)//2]
        specs=(StateEigen(p),StateEigen((p[0],p[1],1)))
        base=Engine(s,Policy(prepare_state=True,state_backend="phase-weighted"))
        e=Engine(s,Policy(prepare_state=True,state_backend="phase-weighted",state_fallback=True))
        out=e.verify(specs)
        assert [r.status for r in out.reports]==["PASS","FAIL"]
        assert out.query_reserved<=2_000_000
        if n==64:
            assert all(r.route=="heisenberg-state" for r in out.reports)
            for spec,r in zip(specs,out.reports):assert replay_report(s,spec,r) is True
        assert e.verify(specs,max_work=1).status=="INCONCLUSIVE"
        rows.append({"n":n,"before":[r.status for r in base.verify(specs).reports],"after":[r.status for r in out.reports],"routes":[r.route for r in out.reports],"timings":measure({"fallback":lambda:e.verify(specs)},reps=9)})
        checks+=3
    return {"checks":checks,"rows":rows,"scope":"exact expectation of zero input via causal-cone sparse Heisenberg propagation; not all-input equivalence"}

if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"ffi":ffi,"fallback":fallback}[sys.argv[1]]()},indent=2,allow_nan=False))
