"""Parallel R19 validation: exact independent Clifford replay, planner and registry."""
import json,random,sys
from itertools import product
import numpy as np
from qiskit.quantum_info import Pauli,Operator
from common5 import circuit,measure
from benchmark import label
from native9 import RustSession
from planner19 import independent_image,independent_verdict,plan_transition,snapshot_id
from library19 import Library

def packed(gs):return bytes(v for g in gs for v in g)
def oracle(n,gs,p):
    u=Operator(circuit(n,gs).to_qiskit()).data
    return u.conj().T@Pauli(label(n,p)).to_matrix()@u
def reject(fn):
    try:fn()
    except (ValueError,TypeError):return
    raise AssertionError("expected rejection")

def independent():
    checks=0; rng=random.Random(1901)
    for op in range(6):
        gs=[(op,0,1 if op==5 else 0)]
        for x,z,s in product(range(4),range(4),(0,1)):
            p=x,z,s;g=packed(gs);r=independent_image(2,g,p)
            np.testing.assert_allclose(Pauli(label(2,r)).to_matrix(),oracle(2,gs,p),atol=1e-10)
            native=RustSession(2,g); assert snapshot_id(2,g)==native.identity
            expected=native.propagate(p); assert expected.terms==((r[0],r[1],(-1)**r[2],0),)
            assert independent_verdict(2,g,r,p)=="PASS"
            assert independent_verdict(2,g,(r[0],r[1],r[2]^1),p)=="FAIL"
            checks+=1
    for n in (2,3,5,8,32,64):
        for j in range(20):
            gs=[]
            for _ in range(50):
                a,b=rng.sample(range(n),2); op=rng.randrange(6);gs.append((op,a,b if op==5 else 0))
            p=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2));g=packed(gs)
            r=independent_image(n,g,p)
            assert RustSession(n,g).propagate(p).terms==((r[0],r[1],(-1)**r[2],0),)
            if n<=5:np.testing.assert_allclose(Pauli(label(n,r)).to_matrix(),oracle(n,gs,p),atol=1e-10)
            checks+=1
    assert independent_image(2,b"\x06\x00\x00",(1,0,0)) is None
    assert independent_image(2,b"\x00\x00\x00",(1,0,0),max_work=1) is None
    reject(lambda:independent_image(2,b"\x05\x00\x00",(1,0,0)))
    return {"checks":checks,"scope":"separate exact Clifford multiplication algorithm; not non-Clifford or strict phase"}

def planner():
    checks=0;rows=[];rng=random.Random(1902)
    for n in (2,3,5):
        for _ in range(20):
            gs=[]
            for j in range(12):
                a,b=rng.sample(range(n),2);op=rng.randrange(8);gs.append((op,a,b if op==5 else 0))
            p=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2));s=RustSession(n,packed(gs))
            for pre in (p,(0,0,0)):
                r=plan_transition(s,pre,p)
                d=oracle(n,gs,p)-Pauli(label(n,pre)).to_matrix()
                assert r.status==("PASS" if np.max(np.abs(d))<1e-10 else "FAIL")
                assert r.reserved<=2_000_000
                if r.status=="FAIL":
                    from test_engine import witness_state
                    w=r.witness;v=witness_state(w);a,b=w.numerator
                    assert abs(np.vdot(v,d@v).real-(a+b*np.sqrt(2))/(1<<w.denominator_power))<1e-9
                checks+=1
    for blocks in (8,16,32):
        n=2*blocks
        # 3 T + 3 Tdg interleaved with Z (commutes with T);
        # separated components avoid global T count and simple adjacent inverse cancellation.
        gs=[g for i in range(blocks) for g in [(5,2*i,2*i+1),(6,2*i,0),(4,2*i,0),(7,2*i,0),(4,2*i,0),(5,2*i,2*i+1)]]
        s=RustSession(n,packed(gs));p=((1<<n)-1,0,0)
        r=plan_transition(s,p,p)
        assert r.status=="PASS" and r.reserved<=2_000_000
        if blocks==32:assert r.attempts[-1].route=="factor"
        assert plan_transition(s,p,p,max_work=1).status=="INCONCLUSIVE"
        bad=plan_transition(s,(p[0],p[1],1),p);assert bad.status=="FAIL" and bad.witness
        rows.append({"width":n,"routes":[a.route for a in r.attempts],"timings":measure({"plan":lambda:plan_transition(s,p,p)},reps=15)})
        checks+=3
    return {"checks":checks,"rows":rows,"scope":"native fallback direct/cone/factor; conservative logical reservations, not memory or wall-time bounds"}

def library():
    n=2;g=packed([(0,0,0),(5,0,1)]);s=RustSession(n,g)
    a,b=(1,0,0),(2,0,0)
    pre_a,pre_b=(independent_image(n,g,p) for p in (a,b))
    old=Library();lib=old.add("a",n,g,pre_a,a).add("b",n,g,pre_b,b)
    assert old.entries==()
    pre,post=lib.product("a","b",n,g)
    assert plan_transition(s,pre,post).status=="PASS"
    np.testing.assert_allclose(oracle(n,[(0,0,0),(5,0,1)],post),Pauli(label(n,pre)).to_matrix(),atol=1e-10)
    reject(lambda:lib.product("a","b",n,g+b"\x00\x00\x00"))
    reject(lambda:lib.add("a",n,g,pre_a,a))
    reject(lambda:old.add("fake",n,g,(pre_a[0],pre_a[1],pre_a[2]^1),a))
    z=(0,1,0);lib=lib.add("z",n,g,independent_image(n,g,z),z)
    reject(lambda:lib.product("a","z",n,g))
    return {"checks":7,"scope":"immutable registry and exact Hermitian product implication on same Clifford snapshot"}
if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"independent":independent,"planner":planner,"library":library}[sys.argv[1]]()},indent=2))
