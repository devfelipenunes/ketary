"""Parallel qualification of native compression, composition, effects and algorithms."""
from common5 import *
from consolidated12 import Engine,Transition
from logical14 import LogicalAction
from native9 import RustSession
from subspace10 import clean
from contracts15 import Action,Clean,compose
from channel15 import ChannelEffect
from front_proof10 import ccx
from front_optimized14 import fixture
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Pauli
from test_engine import witness_state
import ketary as q

def replay(r,rel,n):
    if r.witness is None:return
    psi=witness_state(r.witness);mask=sum(1<<i for i in r.ancillas)
    assert np.linalg.norm(psi[[i for i in range(len(psi)) if i&mask]])<1e-10
    p=Pauli(label(n,r.generator)).to_matrix()
    a,b=r.witness.numerator;expected=(a+b*np.sqrt(2))/(1<<r.witness.denominator_power)
    assert abs(np.vdot(psi,(rel.conj().T@p@rel-p)@psi).real-expected)<1e-10

def projection():
    checks=limits=0;rows=[]
    for n in (4,5,6,8,16,32,64):
        ref=fixture(n,"none");f=Engine.prepare(q.from_qiskit(ref));w=tuple(range(3,n))
        for kind in ("none","ancilla_phase","phase","leak","carry"):
            qc=fixture(n,kind);e=Engine.prepare(q.from_qiskit(qc))
            old=lambda:LogicalAction(w).verify(e,f);new=lambda:Action(w).verify(e,f)
            r=new();assert r.status==old().status==("PASS" if kind in ("none","ancilla_phase") else "FAIL")
            assert r.work_charged<=2_000_000
            if n<=8:replay(r,Operator(ref).data.conj().T@Operator(qc).data,n)
            for work in (1,100,1000):
                assert Action(w).verify(e,f,max_work=work).status==LogicalAction(w).verify(e,f,max_work=work).status;limits+=1
            checks+=1
            if kind in ("none","carry"):
                rows.append({"n":n,"kind":kind,"status":r.status,"timings":measure({"old_python_compression":old,"native_compression":new},reps=21)})
    rng=random.Random(15)
    for n in (2,3,4,5):
        for j in range(16):
            e=Engine.prepare(circuit(n,gates(n,20,j)+[(6,0,0)]));w=tuple(rng.sample(range(n),rng.randint(1,n)))
            r=Clean(w).verify(e);s=clean(e.session,w)
            assert r.status==s.status
            if r.witness:replay(r,Operator(circuit(n,gates(n,20,j)+[(6,0,0)]).to_qiskit()).data,n)
            checks+=1
    output({"scope":"exact projected generators, same status and budget as old route; native canonical witness may differ, replayed independently","checks":checks,"budget_checks":limits,"rows":rows})

def composition():
    rows=[];checks=0
    for n in (4,16,32,64):
        for stages in (2,4,8,16):
            # Each stage is a CNOT fanout with known Pauli transition.
            es=tuple(Engine.prepare(circuit(n,[(5,0,1+i%(n-1))])) for i in range(stages))
            x=1;chain=[(x,0,0)]
            for i in range(stages):x^=1<<(1+i%(n-1));chain.append((x,0,0))
            chain=tuple(chain)
            for kind in ("valid","wrong_middle","wrong_end"):
                ps=list(chain)
                if kind=="wrong_middle":a,b,s=ps[1];ps[1]=(a,b,s^1)
                if kind=="wrong_end":a,b,s=ps[-1];ps[-1]=(a,b,s^1)
                ps=tuple(ps);r=compose(es,ps)
                whole=Engine(RustSession(n,b"".join(e.session.packed for e in es)))
                direct=whole.transitions((Transition(ps[0],ps[-1]),)).checks[0]
                assert r.status==direct.status==("FAIL" if kind=="wrong_end" else "PASS")
                if kind=="wrong_middle":assert r.direct is not None and any(x.status=="FAIL" for x in r.local)
                if kind=="valid":assert r.direct is None
                checks+=1
                if kind=="valid":rows.append({"n":n,"stages":stages,"status":r.status,"timings":measure({"composed":lambda:compose(es,ps),"direct":lambda:whole.transitions((Transition(ps[0],ps[-1]),))},reps=15)})
    output({"scope":"exact sequential Pauli transition; local failure does not imply global failure; direct baseline prepared, composition includes local reports","checks":checks,"rows":rows})

def channels():
    rows=[];checks=0;contract=ChannelEffect()
    for n in (1,2,3,4):
        d=1<<n;id=np.eye(d);z=np.diag([(-1)**(i&1) for i in range(d)]);x=np.kron(np.eye(d//2),np.array([[0,1],[1,0]]));p=(id+x)/2
        for rate in (0.,.01,.25):
            for kind in ("dephase","damp"):
                ks=(np.sqrt(1-rate)*id,np.sqrt(rate)*z) if kind=="dephase" else (np.kron(np.eye(d//2),np.diag([1,np.sqrt(1-rate)])),np.kron(np.eye(d//2),np.array([[0,np.sqrt(rate)],[0,0]])))
                r=contract.verify(p,p,ks);s=contract.verify(p,p,ks,method="superop")
                expected=rate if kind=="dephase" else (1-np.sqrt(1-rate))/2
                assert r.status==s.status==("PASS" if rate==0 else "FAIL") and abs(r.residual-expected)<1e-10 and abs(r.residual-s.residual)<1e-10
                if r.witness:
                    v=np.array(r.witness);rho=np.outer(v,v.conj());gap=np.trace(p@rho-p@sum(k@rho@k.conj().T for k in ks)).real
                    assert abs(gap-r.residual)<1e-10
                checks+=1;rows.append({"n":n,"kind":kind,"rate":rate,"status":r.status,"residual":r.residual,"timings":measure({"kraus":lambda:contract.verify(p,p,ks),"qiskit_superop":lambda:contract.verify(p,p,ks,method="superop")},reps=15)})
    for a,b,ks in ((np.eye(2),np.eye(2),(np.eye(2)*.9,)),(np.eye(32),np.eye(32),(np.eye(32),)),(np.eye(2)*2,np.eye(2),(np.eye(2),))):
        try:contract.verify(a,b,ks)
        except ValueError:pass
        else:raise AssertionError("invalid channel/effect")
    output({"scope":"numeric all-state CPTP effect inequality, not exact proof or channel equivalence; matched numerical report","checks":checks,"rows":rows})

def increment(qc,base,work,k,mutant=False):
    # k active contiguous data wires; k-2 workspace wires allocated.
    for target in reversed(range(2,k)):
        if mutant and target==k-1:continue
        if target==2:ccx(qc,base,base+1,base+2);continue
        ccx(qc,base,base+1,work)
        for j in range(2,target-1):ccx(qc,work+j-2,base+j,work+j-1)
        ccx(qc,work+target-3,base+target-1,base+target)
        for j in reversed(range(2,target-1)):ccx(qc,work+j-2,base+j,work+j-1)
        ccx(qc,base,base+1,work)
    qc.cx(base,base+1);qc.x(base)

def arithmetic():
    rows=[];checks=0
    # Independent matrix permutation up to 5 active bits; large multi-register workloads.
    for k,blocks in ((3,1),(4,1),(5,1),(3,2),(3,4),(3,8),(3,16)):
        n=blocks*(2*k-2);data=blocks*k;w=tuple(range(data,n))
        ref=QuantumCircuit(n)
        for i in range(blocks):increment(ref,i*k,data+i*(k-2),k)
        f=Engine.prepare(q.from_qiskit(ref))
        for kind in ("valid","phase","carry"):
            qc=QuantumCircuit(n)
            # Distinct order of independent blocks. Phase mutant before increment.
            if kind=="phase":qc.z(0)
            for i in reversed(range(blocks)):increment(qc,i*k,data+i*(k-2),k,kind=="carry" and i==0)
            e=Engine.prepare(q.from_qiskit(qc));r=Action(w).verify(e,f)
            if n<=8:
                u=Operator(qc).data[:,:1<<data];v=Operator(ref).data[:,:1<<data]
                target=np.zeros_like(v)
                for x in range(1<<data):
                    y=sum(((((x>>(i*k))&((1<<k)-1))+1)%(1<<k))<<(i*k) for i in range(blocks));target[y,x]=1
                np.testing.assert_allclose(v,target,atol=1e-10)
                phase=np.vdot(v,u)/(1<<data);same=abs(abs(phase)-1)<1e-10 and np.linalg.norm(u-phase*v,2)<1e-10
                assert same==(kind=="valid")
                if r.status!="INCONCLUSIVE":assert r.status==("PASS" if same else "FAIL")
                if r.witness:replay(r,Operator(ref).data.conj().T@Operator(qc).data,n)
            elif r.status!="INCONCLUSIVE":assert r.status==("PASS" if kind=="valid" else "FAIL")
            checks+=1
            rows.append({"n":n,"data":data,"register_bits":k,"blocks":blocks,"gates":len(qc.data),"kind":kind,"status":r.status,"timings":measure({"native_action":lambda:Action(w).verify(e,f)},reps=11)})
    output({"scope":"coherent modular increments, small independent permutation oracle; independent registers at large widths, not single wide adder; retain inconclusive on cap","checks":checks,"rows":rows})

def qec():
    rows=[];checks=0
    for blocks in (1,2,4,8,16):
        n=3*blocks;w=tuple(range(blocks,n))
        for error in (-1,0,1,2):
            for bad in (False,True):
                if error!=0 and bad:continue
                qc=QuantumCircuit(n);ref=QuantumCircuit(n)
                for i in range(blocks):
                    a,b,c=i,blocks+2*i,blocks+2*i+1
                    qc.cx(a,b);qc.cx(a,c)
                    if error>=0:qc.x((a,b,c)[error])
                    qc.cx(a,b);qc.cx(a,c)
                    if not bad or i!=0:ccx(qc,b,c,a)
                    if error in (0,1):ref.x(b)
                    if error in (0,2):ref.x(c)
                e=Engine.prepare(q.from_qiskit(qc));f=Engine.prepare(q.from_qiskit(ref));r=Action(w).verify(e,f)
                assert r.status==("FAIL" if bad else "PASS"),(blocks,error,bad,r)
                if n<=6:
                    u=Operator(qc).data;v=Operator(ref).data;cols=1<<blocks
                    phase=np.vdot(v[:,:cols],u[:,:cols])/cols
                    assert (abs(abs(phase)-1)<1e-10 and np.linalg.norm(u[:,:cols]-phase*v[:,:cols],2)<1e-10)==(not bad)
                    if r.witness:replay(r,v.conj().T@u,n)
                checks+=1
                rows.append({"n":n,"blocks":blocks,"error_wire_per_block":error,"mutant":bad,"status":r.status,"timings":measure({"native_action":lambda:Action(w).verify(e,f)},reps=11)})
    output({"scope":"coherent repetition-code recovery for specified single X error per independent block, syndrome and arbitrary logical input; not general fault tolerance or phase-error correction","checks":checks,"rows":rows})
if __name__=="__main__":
    import sys
    {"projection":projection,"composition":composition,"channels":channels,"arithmetic":arithmetic,"qec":qec}[sys.argv[1]]()
