"""R20 exact oracle, Bell targets and error-set correction tests."""
import json,random,sys
from itertools import product,combinations_with_replacement
import numpy as np
from qiskit.quantum_info import Operator,Pauli
from common5 import circuit,measure
from benchmark import label
from native9 import RustSession
from planner19 import plan_transition
from independent20 import verify_transition,bell_target,correctable_pauli_set
from contract_forms11 import label_mask

def pack(gs):return bytes(v for g in gs for v in g)
def reject(f):
    try:f()
    except ValueError:return
    raise AssertionError("expected rejection")

def exact():
    rng=random.Random(2020);checks=0;rows=[]
    for op in range(8):
        gs=[(op,0,1 if op==5 else 0)]
        for x,z,s in product(range(4),range(4),(0,1)):
            post=x,z,s
            for pre in (post,(x,z,s^1)):
                g=pack(gs);r=verify_transition(2,g,pre,post)
                u=Operator(circuit(2,gs).to_qiskit()).data
                a,b=Pauli(label(2,pre)).to_matrix(),Pauli(label(2,post)).to_matrix()
                delta=u@a-b@u
                assert r.status==("PASS" if np.max(np.abs(delta))<1e-10 else "FAIL")
                if r.status=="FAIL":
                    def val(t):return (t[0]+t[1]*np.sqrt(2)+1j*(t[2]+t[3]*np.sqrt(2)))/(1<<r.denominator_power)
                    assert abs(delta[r.first_difference,r.input_basis]-(val(r.left)-val(r.right)))<1e-10
                checks+=1
    for n in (2,3,4,5):
        for j in range(20):
            gs=[]
            for _ in range(16):
                a,b=rng.sample(range(n),2);op=rng.randrange(8);gs.append((op,a,b if op==5 else 0))
            g=pack(gs);s=RustSession(n,g);post=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))
            # Independent positive control: choose exact native single-image if available.
            r=s.propagate(post)
            t=r.terms;pre=(t[0][0],t[0][1],int(t[0][2]<0)) if len(t)==1 and t[0][3]==0 and abs(t[0][2])==1<<r.denominator_power else post
            for p in (pre,(pre[0],pre[1],pre[2]^1)):
                oracle=verify_transition(n,g,p,post);native=plan_transition(s,p,post)
                assert native.status==oracle.status
                u=Operator(circuit(n,gs).to_qiskit()).data
                assert oracle.status==("PASS" if np.max(np.abs(u@Pauli(label(n,p)).to_matrix()-Pauli(label(n,post)).to_matrix()@u))<1e-9 else "FAIL")
                checks+=1
            if j==0:rows.append({"n":n,"timings":measure({"exact_columns":lambda:verify_transition(n,g,pre,post),"native_plan":lambda:plan_transition(s,pre,post)},reps=9)})
    # Direct Rust cap is not universal: 64 T gates, exact cancellation in U.
    gs=[(6,0,0),(7,0,0)]*32;g=pack(gs);p=(1,0,0)
    assert verify_transition(1,g,p,p).status=="PASS"
    assert verify_transition(1,g,p,p,max_work=1).status=="INCONCLUSIVE"
    reject(lambda:verify_transition(2,b"\x05\x00\x00",p,p))
    return {"checks":checks+3,"rows":rows,"scope":"exact bounded Clifford+T all-basis equality, no general formal proof"}

def bell():
    checks=0
    for n in (2,3,4,5):
        for a,b in product(range(n),repeat=2):
            if a==b:continue
            variants=[([(0,a,0),(5,a,b)],True),([],False),([(0,a,0),(5,a,b),(4,a,0)],False),([(0,a,0),(5,a,b),(3,b,0)],False)]
            if n>=3:
                c=next(i for i in range(n) if i not in (a,b))
                variants += [([(0,a,0),(5,a,b),(0,c,0),(6,c,0)],True), ([(0,a,0),(5,a,b),(5,b,c)],False)]
            for gs,expected in variants:
                r=bell_target(n,pack(gs),a,b)
                u=Operator(circuit(n,gs).to_qiskit()).data[:,0]
                mask=(1<<a)|(1<<b)
                good=all(np.linalg.norm(Pauli(label(n,p)).to_matrix()@u-u)<1e-10 for p in ((mask,0,0),(0,mask,0)))
                assert good==expected and r==("PASS" if good else "FAIL")
                checks+=1
    assert bell_target(2,pack([(0,0,0)]),0,1,max_work=1)=="INCONCLUSIVE"
    reject(lambda:bell_target(2,b"",0,0))
    return {"checks":checks+2,"scope":"exact Bell Phi+ target from zero input; FAIL does not imply separability"}

def codes():
    checks=0;rows=[]
    for name,n,labels,axes in (("repetition",3,("IZZ","ZZI"),(1,)),("five-qubit",5,("IXZZX","XZZXI","ZZXIX","ZXIXZ"),(1,2,3)),("Steane",7,("IIIXXXX","IXXIIXX","XIXIXIX","IIIZZZZ","IZZIIZZ","ZIZIZIZ"),(1,2,3))):
        ss=tuple(label_mask(p,n) for p in labels)
        es=((0,0,0),)+tuple(((1<<i if ax&1 else 0),(1<<i if ax&2 else 0),0) for i in range(n) for ax in axes)
        r=correctable_pauli_set(n,ss,es);assert r.status=="PASS"
        # Independent dense projector: P E†F P proportional to P.
        d=1<<n;P=np.eye(d,dtype=complex)
        for p in ss:P=P@(np.eye(d)+Pauli(label(n,p)).to_matrix())/2
        rank=np.trace(P).real;assert abs(rank-2)<1e-9
        # For the 7-qubit code avoid expensive dense matrix products per pair:
        # use an orthonormal basis for the projector and compare 2x2 blocks.
        vals,vecs=np.linalg.eigh(P);V=vecs[:,vals>0.5]
        images=[Pauli(label(n,p)).to_matrix()@V for p in es]
        for i,j in combinations_with_replacement(range(len(es)),2):
            m=images[i].conj().T@images[j];assert np.linalg.norm(m-np.trace(m)/2*np.eye(2))<1e-9;checks+=1
        logical=((1<<n)-1,0,0)
        bad=correctable_pauli_set(n,ss,((0,0,0),logical));assert bad.status=="FAIL" and bad.pair==(0,1)
        m=V.conj().T@Pauli(label(n,logical)).to_matrix()@V;assert np.linalg.norm(m-np.trace(m)/2*np.eye(2))>0.5
        assert correctable_pauli_set(n,ss,es,max_pairs=1).status=="INCONCLUSIVE"
        checks+=2
        rows.append({"code":name,"width":n,"errors":len(es),"checked_pairs":r.checked_pairs})
    reject(lambda:correctable_pauli_set(2,((3,0,0),(3,0,1)),((0,0,0),)))
    reject(lambda:correctable_pauli_set(2,((1,0,0),(0,1,0)),((0,0,0),)))
    return {"checks":checks+2,"rows":rows,"scope":"exact finite Pauli error set Knill-Laflamme criterion; no implemented recovery claim"}
if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"exact":exact,"bell":bell,"codes":codes}[sys.argv[1]]()},indent=2))
