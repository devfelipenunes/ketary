"""Round 18: independent matrix controls and negative cases per research front."""
from fractions import Fraction as F
from itertools import product
import json,random,sys
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli,Operator
import ketary as q
from consolidated12 import Engine
from contracts18 import exact_sum,dense_sum_residual,phase_compare,z_channel_adjoint,syndrome,compose_error_bounds
from benchmark import label

def raises(f):
    try:f()
    except (ValueError,TypeError):return
    raise AssertionError("expected admission rejection")

def sums():
    checks=0
    # H exchanges X and Z. T†XT=(X-Y)/sqrt(2), so H/T and
    # noncommuting random sums are tested via independent dense residuals.
    for n in (1,2,4,6):
        qc=QuantumCircuit(n);qc.h(0)
        e=Engine.prepare(q.from_qiskit(qc))
        for a,b in ((F(1,3),F(5,7)),(F(-2,5),F(3,11))):
            x=(1,0,0);z=(0,1,0);y=(1,1,0)
            post=((x,a),(z,b),(y,F(1,9)))
            pre=((z,a),(x,b),(y,F(-1,9)))
            for valid in (True,False):
                p=pre if valid else pre+((x,F(1,13)),)
                r=exact_sum(e,p,post)
                assert r.status==("PASS" if valid else "FAIL")
                err=dense_sum_residual(qc,p,post)
                assert err<1e-9 if valid else err>1e-3
                if not valid:assert r.witness and r.residual
                checks+=1
            assert exact_sum(e,pre,post,max_work=1).status=="INCONCLUSIVE";checks+=1
    rng=random.Random(1801)
    for _ in range(40):
        qc=QuantumCircuit(3)
        for k in range(12):
            w=rng.randrange(3)
            if k%4==0:qc.cx(w,(w+1)%3)
            else:(qc.h,qc.t,qc.s)[rng.randrange(3)](w)
        e=Engine.prepare(q.from_qiskit(qc))
        post=tuple(((rng.randrange(8),rng.randrange(8),0),F(rng.randrange(1,5),7)) for _ in range(4))
        pre=post
        r=exact_sum(e,pre,post)
        err=dense_sum_residual(qc,pre,post)
        assert r.status in ("PASS","FAIL") and (err<1e-9)==(r.status=="PASS")
        if r.status=="FAIL":
            axes,signs,pair=r.witness
            psi=np.array([1],complex)
            states={"X":(np.array([1,1]),np.array([1,-1])),"Y":(np.array([1,1j]),np.array([1,-1j])),"Z":(np.array([1,0]),np.array([0,1]))}
            for ax,s in zip(axes,signs):
                v=states[ax][s==-1];psi=np.kron(v/np.linalg.norm(v),psi)
            def mat(terms):
                return sum((float(c)*Pauli(label(3,p)).to_matrix() for p,c in terms),np.zeros((8,8),complex))
            u=Operator(qc).data
            expected=float(pair[0])+float(pair[1])*np.sqrt(2)
            assert abs(expected)>1e-12
            assert abs(np.vdot(psi,(u.conj().T@mat(post)@u-mat(pre))@psi)-expected)<1e-8
        checks+=1
    qc=QuantumCircuit(1);e=Engine.prepare(q.from_qiskit(qc))
    raises(lambda:exact_sum(e,(((1,0,0),0.5),),(((1,0,0),F(1)),)))
    # Exact non-Clifford positive control: T leaves Z fixed, while
    # X+Y cancels with its own negative in the admitted expression.
    qc.t(0);e=Engine.prepare(q.from_qiskit(qc));terms=(((0,1,0),F(2,7)),((1,0,0),F(1,3)),((1,0,1),F(1,3)))
    assert exact_sum(e,terms,terms).status=="PASS";checks+=1
    return {"checks":checks,"scope":"rational Hermitian sums; independent dense propagation controls"}

def phases():
    checks=0
    for n in (1,2,4):
        ref=QuantumCircuit(n);ref.h(0)
        for p in (0.,np.pi/7,np.pi):
            actual=ref.copy();actual.global_phase=p
            status,err=phase_compare(actual,ref)
            assert status==("PASS" if p==0 else "FAIL")
            assert abs(err-abs(np.exp(1j*p)-1))<1e-9
            if n<=2:
                a=QuantumCircuit(n+1);b=a.copy()
                a.append(actual.to_gate().control(),range(n+1))
                b.append(ref.to_gate().control(),range(n+1))
                assert phase_compare(a,b)[0]==status
                checks+=1
            checks+=1
    return {"checks":checks,"scope":"strict numeric phase including controlled-unitary counterexamples"}

def channels():
    checks=0
    for n in (1,2,3):
        for wire in range(n):
            for kind in ("measure","reset"):
                k0=np.array([[1,0],[0,0]]);k1=np.array([[0,0],[0,1]]) if kind=="measure" else np.array([[0,1],[0,0]])
                def lift(a):
                    out=np.array([[1]])
                    for i in range(n):out=np.kron(a if i==wire else np.eye(2),out)
                    return out
                ks=[lift(k0),lift(k1)]
                for x,z,s in product(range(1<<n),range(1<<n),(0,1)):
                    p=x,z,s;mat=Pauli(label(n,p)).to_matrix()
                    r=z_channel_adjoint(n,p,wire,kind)
                    want=np.zeros_like(mat) if r is None else Pauli(label(n,r)).to_matrix()
                    np.testing.assert_allclose(sum(k.conj().T@mat@k for k in ks),want,atol=1e-12)
                    checks+=1
    assert compose_error_bounds((F(1,3),F(1,6)))==F(1,2)
    assert compose_error_bounds((F(3,2),F(3,2)))==2
    raises(lambda:compose_error_bounds((F(-1),)))
    raises(lambda:z_channel_adjoint(2,"IZ",True,"reset"))
    return {"checks":checks+4,"scope":"nonselective Z measurement and reset; conditional branches excluded; analytic CPTP error bound"}

def codes():
    # Bell stabilizers XX, ZZ; generator syndrome cross-checked by matrices.
    checks=0
    for n,ss in ((2,("XX","ZZ")),(3,("IZZ","ZZI")),(5,("IXZZX","XZZXI","ZZXIX","ZXIXZ"))):
        for x,z in product(range(1<<n),repeat=2):
            err=(x,z,0);m=Pauli(label(n,err)).to_matrix()
            actual=syndrome(n,ss,err)
            expected=tuple(int(np.allclose(Pauli(p).to_matrix()@m,-m@Pauli(p).to_matrix())) for p in ss)
            assert actual==expected;checks+=1
    raises(lambda:syndrome(2,("XX","ZI"),"II"))
    raises(lambda:syndrome(2,("XX","-XX"),"II"))
    return {"checks":checks+2,"scope":"independent commuting stabilizer generators and syndrome; no general recovery guarantee"}

if __name__=="__main__":
    print(json.dumps({"suite":sys.argv[1],**{"sums":sums,"phases":phases,"channels":channels,"codes":codes}[sys.argv[1]]()},indent=2))
