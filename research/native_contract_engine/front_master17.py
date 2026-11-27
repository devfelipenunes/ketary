"""Master roadmap W1: existing Observable, strict replay, exact noise."""
from common5 import *
from facade17 import ContractSpec,Policy,verify as check
from consolidated12 import Engine
from evidence17 import record,replay,canonical,sha
from noise17 import NoiseTransition,PauliNoise
from fractions import Fraction
from qiskit.quantum_info import Operator,Pauli
from test_engine import witness_state
from types import SimpleNamespace
from front_optimized14 import fixture
import ketary as q

def forms():
    rows=[];checks=reject=0
    for n in (2,4,8,16,32,62):
        for bad in (False,True):
            c=circuit(n,[(0,0,0)]+[(5,0,i) for i in range(1,n)]+([(4,0,0)] if bad else []));e=Engine.prepare(c)
            p=q.X(0)
            for i in range(1,n):p=p@q.X(i)
            a=ContractSpec.transition(requires=q.Z(0),ensures=p)
            b=ContractSpec.transition(requires="I"*(n-1)+"Z",ensures="X"*n)
            r=check(e,a);assert r==check(e,b) and r.status==("FAIL" if bad else "PASS")
            checks+=2
            if not bad:rows.append({"n":n,"timings":measure({"observable":lambda:check(e,a),"label":lambda:check(e,b)},reps=15)})
    e=Engine.prepare(circuit(2,[]))
    for p in (q.X(0)+q.Z(0),2*q.X(0),0*q.X(0),q.X(2)):
        try:check(e,ContractSpec.invariant(p))
        except ValueError:reject+=1
        else:raise AssertionError("unsupported observable")
    output({"scope":"existing Observable syntax for exact signed single-Pauli contracts, no public change","checks":checks,"rejections":reject,"rows":rows})

def evidence():
    cases=[];reject=0
    for bad in (False,True):
        a=Engine.prepare(circuit(4,[(0,0,0)]+[(5,0,i) for i in range(1,4)]+([(4,0,0)] if bad else [])))
        cases.append((a,ContractSpec.transition(requires=q.Z(0),ensures="XXXX"),None,Policy()))
        b=Engine.prepare(q.from_qiskit(fixture(4,"carry" if bad else "none")));ref=Engine.prepare(q.from_qiskit(fixture(4,"none")))
        for route in ("projected","monomial"):cases.append((b,ContractSpec.action(3),ref,Policy(route=route)))
        cases.append((Engine.prepare(circuit(2,[(3,1,0)] if bad else [])),ContractSpec.clean(1),None,Policy()))
    cases.append((cases[0][0],cases[0][1],None,Policy(max_work=1)))
    cases.append((Engine.prepare(circuit(2,[(0,0,0)])),ContractSpec.action(1),Engine.prepare(circuit(2,[(0,0,0)])),Policy(route="monomial")))
    rows=[]
    for a,c,b,p in cases:
        raw=record(a,c,reference=b,policy=p);assert replay(raw,a,c,reference=b,policy=p)
        d=json.loads(raw);d["body"]["report"]["status"]="PASS" if d["body"]["report"]["status"]!="PASS" else "FAIL"
        d["digest"]=sha(canonical(d["body"]).encode("ascii"))
        for v in (raw+b" ",b'{"body":{},"body":{},"digest":"x"}',b'{"body":NaN,"digest":"x"}',canonical(d).encode("ascii"),b"x"*65537):
            try:replay(v,a,c,reference=b,policy=p)
            except ValueError:reject+=1
            else:raise AssertionError("invalid replay")
        rows.append({"kind":c.kind,"route":p.route,"status":check(a,c,reference=b,policy=p).status,"bytes":len(raw),"timings":measure({"record":lambda:record(a,c,reference=b,policy=p),"replay":lambda:replay(raw,a,c,reference=b,policy=p)},reps=7)})
    output({"scope":"deterministic same-engine reexecution; not independently verified proof or authenticity","checks":len(cases),"rejections":reject,"rows":rows})

def noise():
    rows=[];checks=0
    for n in (2,4,8,16,32,64):
        for layers in (1,4,16):
            for rate in (0,1,4,8):
                z=(0,1,0);x=(1,0,0);s=PauliNoise((((0,0,0),16-rate),(z,rate)),16)
                stages=(s,)*layers;expected=Fraction(16-2*rate,16)**layers
                c=NoiseTransition(x,x,expected);r=c.verify(n,stages);assert r.status=="PASS" and Fraction(*r.coefficient)==expected
                bad=NoiseTransition(x,x,expected-Fraction(1,16) if expected>0 else Fraction(1,16));v=bad.verify(n,stages);assert v.status=="FAIL" and v.witness
                if n<=4:
                    p=Pauli(label(n,x)).to_matrix();zz=Pauli(label(n,z)).to_matrix();adj=p
                    for _ in stages:adj=(16-rate)/16*adj+rate/16*zz@adj@zz
                    np.testing.assert_allclose(adj,float(expected)*p,atol=1e-10)
                    psi=witness_state(SimpleNamespace(axes=v.witness.axes,signs=v.witness.signs))
                    assert abs(np.vdot(psi,(adj-float(bad.coefficient)*p)@psi).real-Fraction(v.witness.numerator,v.witness.denominator))<1e-10
                checks+=2
                if rate==4:rows.append({"n":n,"layers":layers,"coefficient":str(expected),"timings":measure({"exact":lambda:c.verify(n,stages)},reps=15)})
        # Channel order: H then dephasing, E†(X)=(1-2p)Z.
        e=Engine.prepare(circuit(n,[(0,0,0)]));s=PauliNoise((((0,0,0),3),((0,1,0),1)),4)
        c=NoiseTransition((0,1,0),(1,0,0),Fraction(1,2));assert c.verify(n,(e,s)).status=="PASS";assert c.verify(n,(s,e)).status=="FAIL";checks+=2
    output({"scope":"exact rational all-state Pauli transition for restricted noise and Clifford stages; no arbitrary CPTP claim","checks":checks,"rows":rows})
if __name__=="__main__":
    import sys
    {"forms":forms,"evidence":evidence,"noise":noise}[sys.argv[1]]()
