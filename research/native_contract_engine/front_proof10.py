"""Independent dense/analytic references and realistic logical algorithm workloads."""
import argparse,random
from common5 import *
from native9 import RustSession,TransitionContract
from subspace10 import clean
from test_engine import witness_state
from front_d7 import check
from front_channel8 import route
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Pauli
import ketary as q
from dataclasses import asdict

def ccx(c,a,b,t):
    # Exact Toffoli decomposition in the admitted gate alphabet.
    c.h(t);c.cx(b,t);c.tdg(t);c.cx(a,t);c.t(t);c.cx(b,t);c.tdg(t);c.cx(a,t)
    c.t(b);c.t(t);c.h(t);c.cx(a,b);c.t(a);c.tdg(b);c.cx(a,b)
def build_workspace(n,bad):
    c=QuantumCircuit(n);ccx(c,0,1,2);c.cx(2,3)
    if bad!="uncompute":ccx(c,0,1,2)
    if bad=="phase":c.z(0)
    if bad=="action":c.cx(0,3)
    return q.from_qiskit(c)
def independent_clean(c,w):
    u=Operator(c.to_qiskit()).data;mask=sum(1<<i for i in w)
    domain=[i for i in range(len(u)) if not i&mask];outside=[i for i in range(len(u)) if i&mask]
    return float(np.linalg.norm(u[np.ix_(outside,domain)],2)**2),u,domain,outside

def replay_clean(r,u,outside):
    v=witness_state(r.witness);assert np.linalg.norm(v[outside])<1e-10
    assert np.linalg.norm((u@v)[outside])**2>1e-10

def subspace():
    rng=random.Random(102);count=negative=0;rows=[]
    for n in (2,3,4,5):
        for j in range(24):
            gs=[]
            for _ in range(16):
                op=rng.randrange(8);a=rng.randrange(n);b=rng.choice([i for i in range(n) if i!=a]) if op==5 else 0
                gs.append((op,a,b))
            w=tuple(rng.sample(range(n),rng.randrange(1,n+1)))
            # include valid inverse controls and nontrivial clean-preserving gates
            inv={0:0,1:2,2:1,3:3,4:4,5:5,6:7,7:6}
            if j%3==0:gs=gs+[(inv[op],a,b) for op,a,b in reversed(gs)]
            elif j%3==1:gs=[(6,w[0],0),(4,w[0],0)]
            c=circuit(n,gs);s=RustSession.from_circuit(c);r=clean(s,w)
            leak,u,dom,out=independent_clean(c,w)
            assert r.status==("PASS" if leak<1e-10 else "FAIL"),(n,j,w,r,leak)
            if r.status=="FAIL":replay_clean(r,u,out);negative+=1
            count+=1
    # Toffoli workspace restore, mutants and coherent logical action are separate.
    for n in (4,5,8,12,32,64):
        for bad in ("none","uncompute","phase","action"):
            c=build_workspace(n,bad);s=RustSession.from_circuit(c);w=(2,)+tuple(range(4,n))
            r=clean(s,w);expected="FAIL" if bad=="uncompute" else "PASS"
            assert r.status==expected,(n,bad,r)
            # Large-width circuit is an embedded four-wire workload, not a large entangled algorithm.
            if n<=5:
                leak,u,dom,out=independent_clean(c,w)
                assert (leak<1e-10)==(r.status=="PASS")
                ref=np.zeros((1<<n,len(dom)),complex)
                for j,i in enumerate(dom):ref[i^((((i&1)*((i>>1)&1)))<<3),j]=1
                logical=np.linalg.norm(u[:,dom]-ref,2)<1e-10
                assert logical==(bad=="none"),(n,bad,logical)
                if r.status=="FAIL":replay_clean(r,u,out)
            fs={"rust_cold":lambda:clean(RustSession.from_circuit(c),w),"rust_warm":lambda:clean(s,w)}
            if n<=12:fs["numeric_columns"]=lambda:check(c,w,"columns")
            if n<=8:fs["numeric_operator"]=lambda:check(c,w,"operator")
            for name,f in fs.items():
                rr=f();assert (rr.status if name.startswith("rust") else rr[0])==expected
            rows.append({"n":n,"mutant":bad,"status":r.status,"timings":measure(fs,reps=9)})
    c=circuit(16,[(6,i,0) for i in range(13)]+[(0,i,0) for i in range(13)])
    assert clean(RustSession.from_circuit(c),(0,),max_work=1).status=="INCONCLUSIVE"
    for w in ((),(0,0),(True,),(-1,),(16,)):
        try:clean(RustSession.from_circuit(c),w)
        except ValueError:pass
        else:raise AssertionError("invalid wires")
    output({"scope":"exact zero leakage for admitted gates; numerical tolerances separately named; small coherent logical action reference, no claim of whole algorithm correctness at large widths","random_checks":count,"witness_replays":negative,"workspace_checks":len(rows),"rows":rows})

def algorithms():
    rows=[];checks=0
    # Repetition encoding with logical X/Z and every stabilizer transition.
    for n in (3,5,9,16,32,64):
        for mutant in ("none","phase","missing"):
            gs=[(5,0,i) for i in range(1,n) if mutant!="missing" or i!=n-1]
            if mutant=="phase":gs.append((4,0,0))
            c=circuit(n,gs);p=prepare(c);s=RustSession.from_circuit(c)
            obs=(Obligation((1,0,0),((1<<n)-1,0,0)),Obligation((0,1,0),(0,1,0)))+tuple(Obligation((0,1<<i,0),(0,1|(1<<i),0)) for i in range(1,n-1))
            assert len(obs)<=64
            ref=verify(p,obs,method="sparse");got=s.verify(obs)
            def project(rs):return [(r.status,r.obligation_id,r.scope,r.witness) for r in rs]
            assert project(got)==project(ref)
            assert all(r.status=="PASS" for r in got)==(mutant=="none")
            if n<=5:
                u=Operator(c.to_qiskit()).data
                for ob,r in zip(obs,got):
                    delta=u.conj().T@Pauli(label(n,ob.post)).to_matrix()@u-Pauli(label(n,ob.pre)).to_matrix()
                    assert (np.max(np.abs(delta))<1e-10)==(r.status=="PASS")
            checks+=len(obs)
            rows.append({"algorithm":"repetition encoding","n":n,"mutant":mutant,"checks":len(obs),"timings":measure({"python_full":lambda:verify(prepare(c),obs,method="sparse"),"rust_full":lambda:RustSession.from_circuit(c).verify(obs),"rust_warm":lambda:s.verify(obs)},reps=11)})
    # Grover with independent analytic target probability, not Pauli transition.
    for iterations in (1,2):
        for bad in (False,True):
            qc=QuantumCircuit(3);qc.h(range(3))
            for _ in range(iterations):
                if not bad:qc.h(2);ccx(qc,0,1,2);qc.h(2)
                qc.h(range(3));qc.x(range(3));qc.h(2);ccx(qc,0,1,2);qc.h(2);qc.x(range(3));qc.h(range(3))
            c=q.from_qiskit(qc);expected=float(np.sin((2*iterations+1)*np.arcsin(1/np.sqrt(8)))**2)
            f=lambda:q.Contract(3,probabilities={"111":expected}).verify(c.run())
            r=f();assert r.status==("FAIL" if bad else "PASS"),(iterations,bad,r.status)
            rows.append({"algorithm":"Grover snapshot","n":3,"iterations":iterations,"mutant":bad,"status":r.status,"timings":measure({"snapshot":f},reps=11)})
    # Strict QFT operator reference outside native alphabet; no silent fallback.
    for n in (3,4,5):
        for bad in (False,True):
            qc=QuantumCircuit(n)
            for j in reversed(range(n)):
                qc.h(j)
                for k in reversed(range(j)):qc.cp(np.pi/(2**(j-k)),j,k)
            if not bad:
                for i in range(n//2):qc.swap(i,n-1-i)
            c=q.from_qiskit(qc);a=np.arange(1<<n);target=np.exp(2j*np.pi*np.outer(a,a)/(1<<n))/np.sqrt(1<<n)
            f=lambda:float(np.linalg.norm(Operator(c.to_qiskit()).data-target,2))
            assert (f()<1e-10)==(not bad)
            try:RustSession.from_circuit(c)
            except ValueError:pass
            else:raise AssertionError("unsupported QFT admitted")
            rows.append({"algorithm":"QFT strict numeric","n":n,"mutant":bad,"status":"FAIL" if bad else "PASS","timings":measure({"operator":f},reps=11)})
    output({"scope":"matched exact encoding transitions; separate Grover snapshot and QFT strict numeric references, not interchangeable timings","transition_checks":checks,"other_checks":10,"rows":rows})

def cross():
    # Real SDK tests on all three installed platforms without local C ABI compilation.
    count=0
    for n in (2,3,4,5):
        for j in range(10):
            c=circuit(n,gates(n,20,j)+[(6,0,0),(7,0,0),(6,n-1,0)])
            p=prepare(c,allow_t=True);s=RustSession.from_circuit(c)
            rng=random.Random(101+j);post=(rng.getrandbits(n),rng.getrandbits(n),0);ob=Obligation(post,post)
            got=s.verify((ob,))[0];ref=verify(p,(ob,),method="sparse")[0]
            assert (got.status,got.scope,got.witness)==(ref.status,ref.scope,ref.witness)
            u=Operator(c.to_qiskit()).data;delta=u.conj().T@Pauli(label(n,post)).to_matrix()@u-Pauli(label(n,post)).to_matrix()
            assert (np.max(np.abs(delta))<1e-10)==(got.status=="PASS")
            if got.witness:
                w=got.witness;v=witness_state(w);a,b=w.numerator
                assert abs(np.vdot(v,delta@v).real-(a+b*np.sqrt(2))/(1<<w.denominator_power))<1e-10
            count+=1
    output({"scope":"installed native wheel + real SDK dense oracle and deterministic witness parity","checks":count})
if __name__=="__main__":
    import sys
    {"subspace":subspace,"algorithms":algorithms,"cross":cross}[sys.argv[1]]()
