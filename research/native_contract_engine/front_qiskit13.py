"""Qiskit-native baselines, with exact and numerical guarantees kept separate."""
from common5 import *
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford,PauliList,Pauli,Operator,Statevector,SparsePauliOp
from consolidated12 import Engine,Transition,Invariant
from native9 import RustSession
from engine import difference,product_witness,Report,SCOPE,valid_pauli
from test_engine import witness_state
from dataclasses import asdict
from importlib.metadata import version
import ketary as q

def clifford_reports(cl,obs,cid):
    # Qiskit vectorized signed symplectic conjugation, not state simulation.
    n=cl.num_qubits
    values=PauliList([label(n,o.post) for o in obs]).evolve(cl,frame="h")
    out=[]
    for o,p in zip(obs,values):
        x,z,s=bits(p);d=difference(((x,z,(-1)**s,0),),0,o.pre)
        out.append(Report("FAIL" if d else "PASS","qiskit-pauli-list",cid,digest(asdict(o)),SCOPE,"exact signed Pauli comparison",product_witness(n,d,0) if d else None))
    return tuple(out)

def projection(rs):return [(r.status,r.obligation_id,r.scope,r.witness) for r in rs]
def graph(n,bad):
    qc=QuantumCircuit(n);qc.h(range(n))
    edges=sorted({tuple(sorted((i,(i+1)%n))) for i in range(n)}|{(i,i+2) for i in range(0,n-2,3)})
    for a,b in edges:qc.h(b);qc.cx(a,b);qc.h(b)
    if bad:qc.z(0)
    obs=tuple(Obligation((0,1<<i,0),(1<<i,sum(1<<(b if a==i else a) for a,b in edges if i in (a,b)),0)) for i in range(n))
    return qc,obs
def compare_clifford():
    rows=[];checks=0;rng=random.Random(510)
    def case(qc,obs,name,mutant):
        nonlocal checks
        n=qc.num_qubits;c=q.from_qiskit(qc);e=Engine.prepare(c);cid=e.session.identity;cl=Clifford(qc)
        cs=tuple(Transition(o.pre,o.post) for o in obs)
        rust=lambda:e.transitions(cs).checks
        qiskit=lambda:clifford_reports(cl,obs,cid)
        assert projection(rust())==projection(qiskit())
        if n<=5:
            u=Operator(qc).data
            for o,r in zip(obs,rust()):
                d=u.conj().T@Pauli(label(n,o.post)).to_matrix()@u-Pauli(label(n,o.pre)).to_matrix()
                assert (np.max(np.abs(d))<1e-10)==(r.status=="PASS")
                if r.witness:
                    v=witness_state(r.witness);assert abs(np.vdot(v,d@v).real-r.witness.numerator[0])<1e-10
        checks+=len(obs)
        # Common input is already a native QuantumCircuit vs existing Ketary Circuit.
        # Hash is shared fixed provenance, excluded for Qiskit, disclosed separately.
        fs={"ketary_prepared_report":rust,"qiskit_prepared_report":qiskit,
            "ketary_existing_circuit":lambda:Engine.prepare(c).transitions(cs).checks,
            "qiskit_existing_circuit":lambda:clifford_reports(Clifford(qc),obs,cid),
            "qiskit_from_ketary":lambda:clifford_reports(Clifford(c.to_qiskit()),obs,cid)}
        rows.append({"workload":name,"n":n,"gates":len(qc.data),"m":len(obs),"mutant":mutant,"status":[r.status for r in rust()],"timings":measure(fs,reps=21)})
    for n in (4,8,16,32,64):
        for bad in (False,True):case(*graph(n,bad),"graph",bad)
    for n in (16,32,64):
        for g in (100,10000):
            qc=circuit(n,gates(n,g)).to_qiskit();cl=Clifford(qc)
            for m in (1,8,64):
                ps=tuple((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(m))
                pre=[bits(x) for x in PauliList([label(n,p) for p in ps]).evolve(cl,frame="h")]
                obs=tuple(Obligation((x,z,s^(i%2)),p) for i,((x,z,s),p) in enumerate(zip(pre,ps)))
                case(qc,obs,"random Clifford",None)
    output({"scope":"exact Clifford Pauli transition; identical deterministic product witness and report obligation/scope; Qiskit baseline uses same Python witness/report helper and preassigned provenance ID; no hash/admission cost on Qiskit side; existing circuits prepared independently","checks":checks,"qiskit":version("qiskit"),"rows":rows})

def sparse_prepared(qc):
    # Qiskit-native Clifford blocks plus local T conjugation on SparsePauliOp.
    n=qc.num_qubits;blocks=[];block=QuantumCircuit(n)
    for inst in qc.data:
        op=inst.operation;w=[qc.find_bit(b).index for b in inst.qubits]
        if op.name in ("t","tdg"):
            if block.data:blocks.append(("c",Clifford(block)));block=QuantumCircuit(n)
            blocks.append((op.name,w[0]))
        else:block.append(op,w)
    if block.data:blocks.append(("c",Clifford(block)))
    return tuple(reversed(blocks))

def sparse_image(n,post,blocks):
    op=SparsePauliOp.from_list([(label(n,post),1.)])
    for kind,arg in blocks:
        if kind=="c":
            op=op.evolve(arg,frame="h")
        else:
            # T=exp(-i pi Z/8) up to phase. Commuting strings unchanged;
            # anticommuting P -> (P+iZP)/sqrt(2) for T, opposite for Tdg.
            z=Pauli(label(n,(0,1<<arg,0)))
            active=op.paulis.x[:,arg]
            if np.any(active):
                old=op[active];base=op[~active] if np.any(~active) else None
                left=old.compose(SparsePauliOp(z))
                branch=(old+left*(1j if kind=="t" else -1j))*(1/np.sqrt(2))
                op=branch if base is None else base+branch
                op=op.simplify(atol=0.,rtol=0.)
        if len(op)>4096:raise ValueError("numeric term cap")
    return op

def numeric_report(n,ob,blocks):
    op=sparse_image(n,ob.post,blocks)
    delta=(op-SparsePauliOp.from_list([(label(n,ob.pre),1.)])).simplify(atol=0.,rtol=0.)
    # Numerical l1 upper bound on residual in exact arithmetic, not certified roundoff.
    residual=float(np.sum(np.abs(delta.coeffs)))
    return residual,delta

def compare_sparse():
    rows=[];checks=0;rng=random.Random(13)
    # Validate actual implementation vs dense independent oracle first.
    for n in (2,3,4,5):
        for j in range(12):
            gs=gates(n,12,j)+[(6,0,0),(7,n-1,0),(6,n-1,0)]
            c=circuit(n,gs);qc=c.to_qiskit();e=Engine.prepare(c);post=(rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2));ob=Obligation(post,post)
            op=sparse_image(n,post,sparse_prepared(qc));u=Operator(qc).data
            np.testing.assert_allclose(op.to_matrix(),u.conj().T@Pauli(label(n,post)).to_matrix()@u,atol=1e-10)
            checks+=1
    for n in (16,32,64):
        for t in (4,8,12):
            c=circuit(n,[(4,i%n,0) for i in range(100)]+[(6,i,0) for i in range(t)]);qc=c.to_qiskit();e=Engine.prepare(c);blocks=sparse_prepared(qc)
            for kind in ("commuting","branching"):
                post=((1<<n)-1,0,0) if kind=="branching" else (0,(1<<n)-1,0);ob=Obligation(post,post);cs=(Invariant(post),)
                r=e.transitions(cs).checks[0];res,d=numeric_report(n,ob,blocks)
                # All benchmark cases have residual far from the tolerance;
                # exact report compared only for agreement, not equal guarantee.
                assert r.status==("PASS" if res<1e-9 else "FAIL")
                prop=e.session.propagate(post);actual={label(n,(x,z,0)):(a+b*np.sqrt(2))/(1<<prop.denominator_power) for x,z,a,b in prop.terms}
                got=dict(sparse_image(n,post,blocks).to_list())
                assert set(actual)==set(got) and max(abs(actual[k]-got[k]) for k in actual)<1e-10
                # Replay native product witness against the numeric Qiskit polynomial.
                if r.witness:
                    w=r.witness;value=0j
                    for lab,co in d.to_list():
                        prod=1
                        for i,a in enumerate(reversed(lab)):
                            if a!="I":prod*=w.signs[i] if a==w.axes[i] else 0
                        value+=co*prod
                    a,b=w.numerator;assert abs(value-(a+b*np.sqrt(2))/(1<<w.denominator_power))<1e-10
                rows.append({"n":n,"T":t,"kind":kind,"gates":len(qc.data),"status":r.status,"numeric_residual":res,"terms":len(actual),"timings":measure({"ketary_exact_full_report":lambda:Engine.prepare(c).transitions(cs),"ketary_exact_prepared_report":lambda:e.transitions(cs),"qiskit_numeric_full_residual":lambda:numeric_report(n,ob,sparse_prepared(qc)),"qiskit_numeric_prepared_residual":lambda:numeric_report(n,ob,blocks)},reps=15)})
    output({"scope":"same Pauli identity property, distinct exact algebraic vs floating-point residual guarantees; Qiskit residual lacks witness generation and certified roundoff, no performance parity claim; no approximate pruning","qiskit":version("qiskit"),"dense_checks":checks,"rows":rows})

def snapshot():
    rows=[];checks=0
    for n in (4,8,12,16):
        for bad in (False,True):
            qc=QuantumCircuit(n);qc.h(0)
            for i in range(1,n):qc.cx(0,i)
            if bad:qc.z(0)
            c=q.from_qiskit(qc);obs=Pauli("X"*n);contract=q.Contract(n,expectations={"X"*n:1.})
            r=c.run();v=Statevector.from_instruction(qc)
            def qi(s):return "PASS" if abs(complex(s.expectation_value(obs))-1.)<=1e-9 else "FAIL"
            def ke(s):return contract.verify(s).status
            assert ke(r)==qi(v)==("FAIL" if bad else "PASS");checks+=1
            fs={"ketary_snapshot_check":lambda:ke(r),"qiskit_snapshot_check":lambda:qi(v),"ketary_run_and_check":lambda:ke(c.run()),"qiskit_run_and_check":lambda:qi(Statevector.from_instruction(qc))}
            rows.append({"n":n,"gates":len(qc.data),"mutant":bad,"status":ke(r),"timings":measure(fs,reps=21)})
    output({"scope":"public Ketary snapshot Contract vs direct Qiskit Statevector expectation threshold; equal property on zero input, Qiskit returns status only, Ketary report richer; no comparison with universal transition guarantee","qiskit":version("qiskit"),"checks":checks,"rows":rows})
if __name__=="__main__":
    import sys
    {"clifford":compare_clifford,"sparse":compare_sparse,"snapshot":snapshot}[sys.argv[1]]()
