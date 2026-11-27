"""Independent correctness and matched benchmarks of consolidated research engine."""
from common5 import *
from consolidated12 import Engine,Invariant,Transition,CleanAncillas
from native9 import RustSession
from test_engine import witness_state
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Pauli
from front_proof10 import ccx
from dataclasses import asdict
import ketary as q
def project(rs):return [(r.status,r.obligation_id,r.scope,r.witness) for r in rs]
def batch():
    rng=random.Random(20261128);checks=limits=0;rows=[]
    for n in (2,3,4,5):
        for j in range(24):
            gs=gates(n,24,j)+[(6,0,0),(7,0,0),(6,n-1,0)]
            c=circuit(n,gs);e=Engine.prepare(c);u=Operator(c.to_qiskit()).data
            cs=tuple(Transition((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)),(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2))) for _ in range(4))
            obs=tuple(t.obligation(n) for t in cs)
            for adaptive in (False,True):
                got=e.transitions(cs,adaptive=adaptive).checks;ref=e.session.verify(obs,adaptive=adaptive)
                assert project(got)==project(ref)
                for ob,r in zip(obs,got):
                    d=u.conj().T@Pauli(label(n,ob.post)).to_matrix()@u-Pauli(label(n,ob.pre)).to_matrix()
                    assert r.status==("PASS" if np.max(np.abs(d))<1e-10 else "FAIL")
                    if r.witness:
                        w=r.witness;v=witness_state(w);a,b=w.numerator
                        assert abs(np.vdot(v,d@v).real-(a+b*np.sqrt(2))/(1<<w.denominator_power))<1e-10
                    checks+=1
                for terms,work in ((1,2_000_000),(4096,1),(4096,100),(4,200)):
                    assert project(e.transitions(cs,adaptive=adaptive,max_terms=terms,max_work=work).checks)==project(e.session.verify(obs,adaptive=adaptive,max_terms=terms,max_work=work));limits+=len(cs)
    for n in (16,32,64):
        for g in (100,10000):
            c=circuit(n,gates(n,g));e=Engine.prepare(c)
            for m in (1,8,64):
                cs=tuple(Invariant((rng.getrandbits(n),rng.getrandbits(n),0)) for _ in range(m));obs=tuple(x.obligation(n) for x in cs)
                assert project(e.transitions(cs).checks)==project(e.session.verify(obs))
                rows.append({"n":n,"gates":g,"m":m,"timings":measure({"python_dispatch":lambda:e.session.verify(obs),"rust_batch":lambda:e.transitions(cs)},reps=15)})
        c=circuit(n,[(6,1+i%(n-1),0) for i in range(10000)]+[(0,0,0)])
        e=Engine.prepare(c);cs=(Transition((0,1,0),(1,0,0)),);obs=tuple(x.obligation(n) for x in cs)
        assert e.transitions(cs,adaptive=True).status=="PASS"
        assert e.transitions(cs).status=="INCONCLUSIVE"
        rows.append({"n":n,"gates":10001,"m":1,"workload":"causal cone","timings":measure({"python_cone":lambda:e.session.verify(obs,adaptive=True),"rust_cone":lambda:e.transitions(cs,adaptive=True)},reps=15)})
    output({"scope":"identical reports and witness, prepared snapshot, same aggregate propagation budget; preprocessing charge; not full wall time/memory bound","checks":checks,"limit_report_checks":limits,"rows":rows})
def eq():
    rng=random.Random(49);rows=[];checks=0
    for n in (2,3,4,5):
        for j in range(12):
            gs=gates(n,14,j)+[(6,0,0)]
            a=circuit(n,gs);u=Operator(a.to_qiskit()).data
            for mode in ("same","phase","mutant","inverse_pair"):
                qc=a.to_qiskit()
                if mode=="phase":qc.global_phase=.27
                if mode=="mutant":qc.z(0)
                if mode=="inverse_pair":qc.t(0);qc.tdg(0)
                b=q.from_qiskit(qc);v=Operator(qc).data
                phase=np.vdot(v,u)/len(u);expected=abs(abs(phase)-1)<1e-10 and np.max(np.abs(u-phase*v))<1e-10
                e,f=Engine.prepare(a),Engine.prepare(b);r=e.equivalent(f)
                assert r.status==("PASS" if expected else "FAIL"),(n,j,mode,r.status)
                if mode=="phase":assert np.linalg.norm(u-v,2)>.1
                for x in r.checks:
                    if x.witness:
                        # Relative operation V†U. Recover generator by report ID.
                        for i in range(n):
                            for p in ((1<<i,0,0),(0,1<<i,0)):
                                if digest(asdict(Obligation(p,p)))==x.obligation_id:
                                    rel=v.conj().T@u;pa=Pauli(label(n,p)).to_matrix();d=rel.conj().T@pa@rel-pa
                                    w=x.witness;psi=witness_state(w);aa,bb=w.numerator
                                    assert abs(np.vdot(psi,d@psi).real-(aa+bb*np.sqrt(2))/(1<<w.denominator_power))<1e-10
                checks+=1
    for n in (4,8,16,32):
        gs=gates(n,100,n);a=circuit(n,gs);b=circuit(n,gs+[(6,0,0),(7,0,0)])
        e,f=Engine.prepare(a),Engine.prepare(b)
        assert e.equivalent(f).status=="PASS"
        assert e.equivalent(f,max_work=1).status=="INCONCLUSIVE"
        rows.append({"n":n,"gates":len(gs),"timings":measure({"rust_equivalence_warm":lambda:e.equivalent(f),"rust_equivalence_cold":lambda:Engine.prepare(a).equivalent(Engine.prepare(b))},reps=15)})
    output({"scope":"full unitary equivalence up to global phase; admitted gate alphabet; relative witness; not strict phase; max 32 wires","dense_checks":checks,"rows":rows})
def algorithms():
    rows=[];checks=0
    # Graph-state preparation: independent graph adjacency defines stabilizers.
    for n in (4,8,16,32,64):
        edges=sorted({tuple(sorted((i,(i+1)%n))) for i in range(n)}|{(i,i+2) for i in range(0,n-2,3)})
        for bad in (False,True):
            qc=QuantumCircuit(n);qc.h(range(n))
            for a,b in edges:qc.h(b);qc.cx(a,b);qc.h(b)
            if bad:qc.z(0)
            c=q.from_qiskit(qc);e=Engine.prepare(c)
            cs=tuple(Transition((0,1<<i,0),(1<<i,sum(1<<(b if a==i else a) for a,b in edges if i in (a,b)),0)) for i in range(n))
            obs=tuple(x.obligation(n) for x in cs);p=prepare(c)
            r=e.transitions(cs);ref=verify(p,obs,method="sparse")
            assert project(r.checks)==project(ref) and r.status==("FAIL" if bad else "PASS")
            if n<=8:
                u=Operator(qc).data
                for ob,v in zip(obs,r.checks):assert (np.max(np.abs(u.conj().T@Pauli(label(n,ob.post)).to_matrix()@u-Pauli(label(n,ob.pre)).to_matrix()))<1e-10)==(v.status=="PASS")
            checks+=len(cs)
            rows.append({"algorithm":"graph state stabilizer transitions","n":n,"gates":len(qc.data),"mutant":bad,"status":r.status,"checks":len(cs),"timings":measure({"python_cold":lambda:verify(prepare(c),obs,method="sparse"),"rust_cold":lambda:Engine.prepare(c).transitions(cs),"rust_warm":lambda:e.transitions(cs)},reps=15)})
    # QAOA-style ring cost and mixer at pi/4 rotation, global X symmetry.
    # No claim of solving MaxCut or certifying optimality.
    for n,depth in ((4,1),(4,2),(8,1),(8,2),(16,1)):
        for bad in (False,True):
            qc=QuantumCircuit(n)
            for _ in range(depth):
                for i in range(n):
                    j=(i+1)%n;qc.cx(i,j);qc.t(j);qc.cx(i,j)
                for i in range(n):qc.h(i);qc.t(i);qc.h(i)
            if bad:qc.z(0)
            c=q.from_qiskit(qc);e=Engine.prepare(c);cs=(Invariant("X"*n),);obs=(cs[0].obligation(n),)
            r=e.transitions(cs);ref=verify(prepare(c,allow_t=True),obs,method="sparse")
            assert project(r.checks)==project(ref) and r.status==("FAIL" if bad else "PASS"),(n,depth,bad,r)
            if n<=8:
                u=Operator(qc).data;p=Pauli("X"*n).to_matrix()
                assert (np.max(np.abs(u.conj().T@p@u-p))<1e-10)==(not bad)
            checks+=1
            rows.append({"algorithm":"QAOA ring symmetry","n":n,"depth":depth,"gates":len(qc.data),"mutant":bad,"status":r.status,"checks":1,"timings":measure({"python_cold":lambda:verify(prepare(c,allow_t=True),obs,method="sparse"),"rust_cold":lambda:Engine.prepare(c).transitions(cs),"rust_warm":lambda:e.transitions(cs)},reps=15)})
    # Two-bit modular adder, all coherent inputs, independent permutation.
    for bad in ("none","phase","carry"):
        qc=QuantumCircuit(4);qc.cx(1,3)
        if bad!="carry":ccx(qc,0,2,3)
        qc.cx(0,2)
        if bad=="phase":qc.z(0)
        c=q.from_qiskit(qc);u=Operator(qc).data
        target=np.zeros((16,16),complex)
        for i in range(16):target[(i&3)|((((i>>2)+(i&3))%4)<<2),i]=1
        assert (np.linalg.norm(u-target,2)<1e-10)==(bad=="none")
        # Alternative ordering of commuting operations on y1.
        base=QuantumCircuit(4);ccx(base,0,2,3);base.cx(1,3);base.cx(0,2)
        b=q.from_qiskit(base);e,f=Engine.prepare(c),Engine.prepare(b)
        r=e.equivalent(f);assert r.status==("PASS" if bad=="none" else "FAIL")
        checks+=1
        rows.append({"algorithm":"two-bit modular adder coherent equivalence","n":4,"gates":len(qc.data),"mutant":bad,"status":r.status,"checks":8,"timings":measure({"rust_equivalence":lambda:e.equivalent(f),"dense_strict_reference":lambda:float(np.linalg.norm(Operator(c.to_qiskit()).data-target,2))},reps=15)})
    output({"scope":"graph state stabilizer transitions, QAOA symmetry only, full up-to-phase adder vs separate strict dense permutation; no optimization/whole QAOA claim","checks":checks,"rows":rows})
if __name__=="__main__":
    import sys
    {"batch":batch,"equivalence":eq,"algorithms":algorithms}[sys.argv[1]]()
