"""Round 16: resolve symbolic caps and qualify scalable composition."""
from common5 import *
from consolidated12 import Engine,Transition
from contracts15 import Action,compose
from monomial16 import MonomialAction,action
from channel16 import SequentialEffect
from front_roadmap15 import increment
from front_proof10 import ccx
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import ketary as q

def monomial():
    rows=[];checks=0
    # The recognized CCX macro is exact including phase, not relative-phase Toffoli.
    qc=QuantumCircuit(3);ccx(qc,0,1,2);ref=QuantumCircuit(3);ref.ccx(0,1,2)
    np.testing.assert_allclose(Operator(qc).data,Operator(ref).data,atol=1e-12)
    for k,blocks in ((3,1),(4,1),(5,1),(6,1),(8,1),(3,2),(3,4),(3,8),(3,16)):
        n=blocks*(2*k-2);data=blocks*k;w=tuple(range(data,n));ref=QuantumCircuit(n)
        for i in range(blocks):increment(ref,i*k,data+i*(k-2),k)
        b=Engine.prepare(q.from_qiskit(ref))
        for kind in ("valid","phase","carry"):
            qc=QuantumCircuit(n)
            if kind=="phase":qc.z(0)
            for i in reversed(range(blocks)):increment(qc,i*k,data+i*(k-2),k,kind=="carry" and i==0)
            a=Engine.prepare(q.from_qiskit(qc));c=MonomialAction(w);r=c.verify(a,b);old=Action(w).verify(a,b)
            assert r.status==("PASS" if kind=="valid" else "FAIL"),(n,kind,r)
            assert old.status in (r.status,"INCONCLUSIVE")
            if n<=8:
                u=Operator(qc).data;v=Operator(ref).data
                dom=1<<data;target=np.zeros((1<<n,dom),complex)
                for x in range(dom):
                    y=sum(((((x>>(i*k))&((1<<k)-1))+1)%(1<<k))<<(i*k) for i in range(blocks));target[y,x]=1
                np.testing.assert_allclose(v[:,:dom],target,atol=1e-10)
                phase=np.vdot(v[:,:dom],u[:,:dom])/dom
                assert (abs(abs(phase)-1)<1e-10 and np.linalg.norm(u[:,:dom]-phase*v[:,:dom],2)<1e-10)==(kind=="valid")
                if r.evidence:
                    mask,x0,x1,y,z,p0,p1=r.evidence
                    assert (x0|x1)<dom
                    if r.reason=="basis output differs":assert np.argmax(abs(u[:,x0]))!=np.argmax(abs(v[:,x0]))
                    else:
                        a0=np.vdot(v[:,x0],u[:,x0]);a1=np.vdot(v[:,x1],u[:,x1])
                        assert abs(a0-a1)>1e-10 and abs(a1/a0-np.exp(1j*np.pi*(p1-p0)/4))<1e-10
            checks+=1
            rows.append({"n":n,"data":data,"k":k,"blocks":blocks,"kind":kind,"status":r.status,"old_status":old.status,"work":r.work_charged,"timings":measure({"monomial":lambda:c.verify(a,b),"projected":lambda:Action(w).verify(a,b),"planner":lambda:action(a,b,w)},reps=11)})
    e=Engine.prepare(circuit(2,[(0,0,0)]));assert MonomialAction((1,)).verify(e,e).status=="UNSUPPORTED"
    assert action(e,e,(1,)).status=="PASS"
    e=Engine.prepare(circuit(2,[(3,0,0)]));assert MonomialAction((1,)).verify(e,e,max_work=1).status=="INCONCLUSIVE"
    # Exhaustive signed phase controls, including all-clean input and wire 63.
    for n in (2,64):
        for op in (1,2,4,6,7):
            a=Engine.prepare(circuit(n,[(op,n-1,0)]));b=Engine.prepare(circuit(n,[]))
            assert MonomialAction((n-1,)).verify(a,b).status=="PASS"
            assert MonomialAction((0,)).verify(a,b).status=="FAIL"
            checks+=2
    output({"scope":"exact recognized monomial clean-domain action; component basis enumeration includes coherent relative phase; unsupported H patterns not admitted; same full action as projected; large workloads independent registers","checks":checks,"rows":rows})

def composition():
    rows=[];checks=0
    for n in (4,16,32,64):
        for count in (4,8,16):
            es=tuple(Engine.prepare(circuit(n,[(6,0,0)]*8)) for _ in range(count))
            z=(0,1,0);chain=(z,)*(count+1);whole=Engine(__import__("native9").RustSession(n,b"".join(e.session.packed for e in es)))
            a=lambda:compose(es,chain);b=lambda:whole.transitions((Transition(z,z),),adaptive=True)
            assert a().status=="PASS"
            assert b().status==("PASS" if count==4 else "INCONCLUSIVE")
            checks+=1
            rows.append({"n":n,"stages":count,"T":count*8,"status":a().status,"direct_status":b().status,"timings":measure({"composed":a,"direct":b},reps=21)})
    output({"scope":"exact same Pauli property; staged proof increases coverage under fixed T cap, not speedup when direct inconclusive","checks":checks,"rows":rows})

def channels():
    rows=[];checks=0;c=SequentialEffect()
    for n in (1,2,3,4):
        d=1<<n;id=np.eye(d);z=np.diag([(-1)**(i&1) for i in range(d)]);x=np.kron(np.eye(d//2),np.array([[0,1],[1,0]]));p=(id+x)/2
        for rate in (0.,.01,.25):
            ks=(np.sqrt(1-rate)*id,np.sqrt(rate)*z)
            for layers in (1,4,16):
                stages=(ks,)*layers;r=c.verify(p,p,stages);s=c.verify(p,p,stages,method="superop");expected=(1-(1-2*rate)**layers)/2
                assert r.status==s.status==("PASS" if rate==0 else "FAIL") and abs(r.residual-expected)<1e-10 and abs(s.residual-expected)<1e-10
                if r.witness:assert abs(r.replay_gap-expected)<1e-10
                checks+=1
                rows.append({"n":n,"layers":layers,"rate":rate,"status":r.status,"residual":r.residual,"timings":measure({"kraus_sequence":lambda:c.verify(p,p,stages),"qiskit_superop_sequence":lambda:c.verify(p,p,stages,method="superop")},reps=11)})
    output({"scope":"numerical same all-state effect inequality for sequential CPTP channels; analytic dephasing composition; no certified roundoff","checks":checks,"rows":rows})
if __name__=="__main__":
    import sys
    {"monomial":monomial,"composition":composition,"channels":channels}[sys.argv[1]]()
