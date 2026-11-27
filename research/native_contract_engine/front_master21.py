"""R21: connected cuts, DD compression, actual recovery actions and held-out algorithms."""
import json,random,sys,tracemalloc,resource
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from itertools import product
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Statevector,Pauli
from common5 import circuit,measure
from benchmark import label
from native9 import RustSession
from planner19 import plan_transition
from cuts21 import cuts,check_certificate,adaptive
from structures21 import compress,expand,state_dag,recovery_table,correction,normalize
from independent20 import column,admit,verify_transition
from contract_forms11 import label_mask
import ketary_native_research as rn

def pack(gs):return bytes(v for g in gs for v in g)
def output(x):print(json.dumps(x,indent=2,allow_nan=False))
def reject(f):
    try:f()
    except (ValueError,TypeError,OverflowError):return
    raise AssertionError("admitted malformed input")

def composition():
    rows=[];checks=0
    for n in (2,4,8,16,32,64):
        # Connected ring, with each T Z Tdg Z block identity, not adjacent inverses.
        gs=[]
        for i in range(n):
            gs.extend([(6,i,0),(4,i,0),(7,i,0),(4,i,0)])
        # A connected compute/uncompute chain, identity overall.
        chain=[(5,i,i+1) for i in range(n-1)]
        gs+=chain+list(reversed(chain))
        g=pack(gs);s=RustSession(n,g);p=((1<<n)-1,0,0)
        # Four-gate T blocks and 2-gate Clifford segments; chunk boundaries
        # align with non-Clifford local blocks when cutting from the end.
        if len(gs)%4:gs.extend([(4,0,0),(4,0,0)]);g=pack(gs);s=RustSession(n,g)
        c=cuts(s,p,p,chunk=4)
        assert c and check_certificate(n,g,p,p,c)
        bad=replace(c,segments=(replace(c.segments[0],post=(p[0],p[1],1)),)+c.segments[1:])
        assert not check_certificate(n,g,p,p,bad)
        assert not check_certificate(n,g,p,p,replace(c,circuit_id="0"*64))
        assert not check_certificate(n,g,p,p,replace(c,segments=c.segments[1:]))
        assert not check_certificate(n,g,p,p,c,max_work=1)
        if n<=4:assert verify_transition(n,g,p,p).status=="PASS"
        r=plan_transition(s,p,p)
        rows.append({"n":n,"gates":len(gs),"segments":len(c.segments),"baseline_status":r.status,"timings":measure({"produce":lambda:cuts(s,p,p,chunk=4),"check":lambda:check_certificate(n,g,p,p,c)},reps=9)})
        checks+=5
    for n in (8,32,64):
        gs=[(6,1+i%(n-1),0) for i in range(128)]+[(0,0,0)]
        s=RustSession(n,pack(gs));pre=(0,1,0);post=(1,0,0)
        assert adaptive(s,pre,post)[1]=="PASS"
        rows.append({"n":n,"case":"irrelevant T","timings":measure({"baseline":lambda:plan_transition(s,pre,post),"adaptive":lambda:adaptive(s,pre,post)},reps=15)})
        checks+=1
    return {"checks":checks,"rows":rows,"scope":"temporal Pauli cuts, not arbitrary spatial cutting"}

def dag():
    checks=0;rows=[]
    for n in (2,3,4,5):
        for gs in ([],[(0,i,0) for i in range(n)],[(0,0,0)]+[(5,0,i) for i in range(1,n)],[(0,i,0) for i in range(n)]+[(6,i,0) for i in range(n)]):
            g=pack(gs);v,k=column(n,admit(n,g,2_000_000),0);d=state_dag(n,g)
            assert expand(d)==normalize(v,k)
            assert compress(v,k,n,max_nodes=1) is None
            rows.append({"n":n,"nodes":len(d.nodes),"dense_tree_nodes":2*(1<<n)-1,"denominator_before":k,"denominator_after":d.denominator})
            checks+=2
    return {"checks":checks,"rows":rows,"scope":"post-compression exact unweighted amplitude DAG, not DD gate execution"}

def recovery():
    checks=0;rows=[]
    for n,labels,axes in ((3,("IZZ","ZZI"),(1,)),(5,("IXZZX","XZZXI","ZZXIX","ZXIXZ"),(1,2,3)),(7,("IIIXXXX","IXXIIXX","XIXIXIX","IIIZZZZ","IZZIIZZ","ZIZIZIZ"),(1,2,3))):
        ss=tuple(label_mask(p,n) for p in labels)
        es=((0,0,0),)+tuple((int(bool(ax&1))<<i,int(bool(ax&2))<<i,0) for i in range(n) for ax in axes)
        t=recovery_table(n,ss,es);assert t.status=="PASS"
        d=1<<n;P=np.eye(d,dtype=complex)
        for p in ss:P=P@(np.eye(d)+Pauli(label(n,p)).to_matrix())/2
        vals,vecs=np.linalg.eigh(P);V=vecs[:,vals>0.5];assert V.shape[1]==2
        for e in es:
            c=correction(n,ss,e,t);assert c is not None
            W=Pauli(label(n,c)).to_matrix()@(Pauli(label(n,e)).to_matrix()@V)
            phase=np.trace(V.conj().T@W)/2
            assert abs(abs(phase)-1)<1e-9 and np.linalg.norm(W-phase*V)<1e-9
            checks+=1
        rows.append({"n":n,"errors":len(es),"syndromes":len(t.table)})
    return {"checks":checks,"rows":rows,"scope":"ideal syndrome-conditioned Pauli correction on code space; not physical extraction"}

def algorithms():
    checks=0;rows=[]
    from qiskit.circuit.library import QFTGate
    for n in (2,3,4,5):
        q=QuantumCircuit(n);q.append(QFTGate(n),range(n));u=Operator(q).data;d=1<<n
        oracle=np.exp(2j*np.pi*np.outer(np.arange(d),np.arange(d))/d)/np.sqrt(d)
        np.testing.assert_allclose(u,oracle,atol=1e-10);checks+=1
        # Grover, one iteration, one marked basis state.
        target=d-1;v=np.ones(d)/np.sqrt(d);z=np.eye(d);z[target,target]=-1
        got=(2*np.outer(v,v)-np.eye(d))@z@v
        np.testing.assert_allclose(abs(got[target])**2,np.sin(3*np.arcsin(1/np.sqrt(d)))**2,atol=1e-10);checks+=1
        # QPE with exactly representable phase, controlled powers synthesized.
        phase=1/d;q=QuantumCircuit(n+1);q.x(n)
        for i in range(n):q.h(i);q.cp(2*np.pi*phase*(1<<i),i,n)
        q.append(QFTGate(n).inverse(),range(n));sv=Statevector.from_instruction(q)
        assert abs(sv.data[d+1])**2>1-1e-10;checks+=1
        # Variational expectation and parameter shift; numerical reference only.
        for t in (.1,.7,1.9):
            def energy(a):
                c=QuantumCircuit(1);c.ry(a,0);return float(Statevector.from_instruction(c).expectation_value(Pauli("Z")).real)
            assert abs(energy(t)-np.cos(t))<1e-10
            assert abs((energy(t+np.pi/2)-energy(t-np.pi/2))/2+np.sin(t))<1e-10;checks+=2
        # QAOA one layer for a single MaxCut edge; compare dense independent formula.
        beta,gamma=.37,.83;c=QuantumCircuit(2);c.h([0,1]);c.rzz(gamma,0,1);c.rx(2*beta,[0,1])
        zz=Pauli("ZZ").to_matrix();x=Pauli("X").to_matrix();rx=np.cos(beta)*np.eye(2)-1j*np.sin(beta)*x
        ref=np.kron(rx,rx)@np.diag(np.exp(-1j*gamma*np.diag(zz)/2))@np.ones(4)/2
        np.testing.assert_allclose(Statevector.from_instruction(c).data,ref,atol=1e-10);checks+=1
        rows.append({"n":n,"qft_grover_qpe_vqe_qaoa":"numeric reference fixtures; not native admission"})
    return {"checks":checks,"rows":rows,"scope":"algorithmic oracle fixtures only; arbitrary rotations not admitted by exact native engine"}

def native():
    rng=random.Random(2101);checks=0;rows=[]
    for n in (8,32,64):
        gs=[]
        for _ in range(512):
            a,b=rng.sample(range(n),2);op=rng.randrange(6);gs.append((op,a,b if op==5 else 0))
        s=RustSession(n,pack(gs));ps=tuple((rng.getrandbits(n),rng.getrandbits(n),0) for _ in range(64))
        obs=tuple((p,p) for p in ps)
        def scalar():return tuple(s.native.transition(a,b,4096,2_000_000) for a,b in obs)
        def batch():return tuple(s.native.transition_batch(obs,4096,2_000_000,False))
        with ThreadPoolExecutor(max_workers=4) as pool:
            def threaded():return tuple(pool.map(lambda ab:s.native.transition(*ab,4096,2_000_000),obs))
            a,b,c=scalar(),batch(),threaded()
            # Work accounting can differ; compare statuses and exact witnesses.
            assert [r[:2] for r in a]==[r[:2] for r in b]==[r[:2] for r in c]
            timings=measure({"scalar":scalar,"bitslice":batch,"threads4":threaded},reps=15)
        tracemalloc.start();batch();_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        rows.append({"n":n,"timings":timings,"python_peak_bytes":peak,"process_highwater_kib_linux":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss});checks+=64
    for n,g in ((True,b""),(0,b""),(65,b""),(2,b"\x05\x00\x00"),(2,b"\x09\x00\x00"),(2,b"\x00"),(2,b"\x00\x02\x00")):
        reject(lambda:rn.PackedCircuit(n,g));checks+=1
    s=RustSession(2,b"")
    for p in ((4,0,0),(0,0,2),(-1,0,0)):
        reject(lambda:s.native.propagate(p,4096,100));checks+=1
    return {"checks":checks,"rows":rows,"scope":"native scalar/bitslice/thread pilot; tracemalloc excludes Rust allocations, RSS is process highwater"}
if __name__=="__main__":
    output({"suite":sys.argv[1],**{"composition":composition,"dag":dag,"recovery":recovery,"algorithms":algorithms,"native":native}[sys.argv[1]]()})
