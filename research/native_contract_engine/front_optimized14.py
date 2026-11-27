"""Native Clifford bit slicing and coherent logical-action qualification."""
from common5 import *
from consolidated12 import Engine,Transition
from native9 import RustSession
from logical14 import LogicalAction
from front_qiskit13 import clifford_reports,projection,graph
from front_proof10 import ccx
from qiskit.quantum_info import Clifford,PauliList,Operator
from qiskit import QuantumCircuit
from test_engine import witness_state
import ketary as q

def batch():
    rng=random.Random(141);checks=limits=0;rows=[]
    for n in (2,4,16,32,64):
        for g in (0,12,100):
            qc=circuit(n,gates(n,g,141)).to_qiskit();e=Engine.prepare(q.from_qiskit(qc));cl=Clifford(qc)
            for m in (1,7,8,31,64):
                ps=tuple((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(m))
                pre=[bits(p) for p in PauliList([label(n,p) for p in ps]).evolve(cl,frame="h")]
                obs=tuple(Obligation((x,z,s^(i%2)),p) for i,((x,z,s),p) in enumerate(zip(pre,ps)))
                cs=tuple(Transition(o.pre,o.post) for o in obs)
                got=e.transitions(cs).checks
                assert projection(got)==projection(e.session.verify(obs))==projection(clifford_reports(cl,obs,e.session.identity))
                checks+=m
                for budget in sorted({1,max(1,g-1),max(1,g),max(1,g*m-1),max(1,g*m)}):
                    assert projection(e.transitions(cs,max_work=budget).checks)==projection(e.session.verify(obs,max_work=budget));limits+=m
    for n in (16,32,64):
        for g in (100,10000):
            qc=circuit(n,gates(n,g,14)).to_qiskit();c=q.from_qiskit(qc);e=Engine.prepare(c);cl=Clifford(qc)
            for m in (1,8,64):
                ps=tuple((rng.getrandbits(n),rng.getrandbits(n),rng.randrange(2)) for _ in range(m))
                pre=[bits(p) for p in PauliList([label(n,p) for p in ps]).evolve(cl,frame="h")]
                obs=tuple(Obligation((x,z,s^(i%2)),p) for i,((x,z,s),p) in enumerate(zip(pre,ps)))
                cs=tuple(Transition(o.pre,o.post) for o in obs)
                fs={"rust_scalar_dispatch":lambda:e.session.verify(obs),"rust_batch":lambda:e.transitions(cs).checks,"qiskit_prepared":lambda:clifford_reports(cl,obs,e.session.identity),"rust_cold":lambda:Engine.prepare(c).transitions(cs).checks,"qiskit_cold":lambda:clifford_reports(Clifford(qc),obs,e.session.identity)}
                assert len({tuple(projection(f())) for f in fs.values()})==1
                rows.append({"n":n,"gates":g,"m":m,"timings":measure(fs,reps=21)})
    output({"scope":"exact Clifford reports, deterministic witness parity; conservative original scalar gate-visit budget unchanged; Qiskit uses preassigned provenance and Python report helper","checks":checks,"budget_checks":limits,"rows":rows})
def fixture(n,kind):
    # Increment low three data bits modulo 8, remaining wires clean.
    # Alternative pre-action on ancilla |0> is allowed; data phase is not.
    qc=QuantumCircuit(n)
    if kind=="ancilla_phase":qc.z(3)
    if kind=="phase":qc.z(0)
    if kind=="leak":qc.cx(0,3)
    if kind!="carry":ccx(qc,0,1,2)
    qc.cx(0,1);qc.x(0)
    return qc
def logical():
    checks=0;rows=[]
    for n in (4,5,6,8,16,32,64):
        ref=fixture(n,"none");w=tuple(range(3,n));f=Engine.prepare(q.from_qiskit(ref));contract=LogicalAction(w)
        for kind in ("none","ancilla_phase","phase","leak","carry"):
            qc=fixture(n,kind);c=q.from_qiskit(qc);e=Engine.prepare(c)
            r=contract.verify(e,f);expected=kind in ("none","ancilla_phase")
            assert r.status==("PASS" if expected else "FAIL"),(n,kind,r)
            if n<=8:
                u=Operator(qc).data[:,:8];v=Operator(ref).data[:,:8]
                target=np.zeros_like(v)
                for i in range(8):target[(i+1)%8,i]=1
                np.testing.assert_allclose(v,target,atol=1e-10)
                phase=np.vdot(v,u)/8
                assert (abs(abs(phase)-1)<1e-10 and np.linalg.norm(u-phase*v,2)<1e-10)==expected
                if r.witness:
                    psi=witness_state(r.witness);assert np.linalg.norm(psi[8:])<1e-10
                    # Witness is for a relative compressed generator; find the stated generator
                    # by checking all admitted generators independently.
                    rel=Operator(ref).data.conj().T@Operator(qc).data
                    aa,bb=r.witness.numerator;gap=(aa+bb*np.sqrt(2))/(1<<r.witness.denominator_power)
                    ps=[(0,1<<i,0) for i in w]+[p for i in range(3) for p in ((1<<i,0,0),(0,1<<i,0))]
                    assert any(abs(np.vdot(psi,(rel.conj().T@Pauli(label(n,p)).to_matrix()@rel-Pauli(label(n,p)).to_matrix())@psi).real-gap)<1e-10 for p in ps)
            checks+=1
            if n in (4,8,32,64):
                rows.append({"n":n,"data":3,"gates":len(qc.data),"kind":kind,"status":r.status,"timings":measure({"rust_logical_warm":lambda:contract.verify(e,f),"rust_logical_cold":lambda:contract.verify(Engine.prepare(c),Engine.prepare(q.from_qiskit(ref)))},reps=15)})
        assert contract.verify(f,f,max_work=1).status=="INCONCLUSIVE"
    output({"scope":"all coherent clean inputs, common global phase only; 3-bit modular increment embedded at large widths, not a 64-bit adder; independent isometry oracle through 8q","checks":checks,"rows":rows})
if __name__=="__main__":
    import sys
    {"batch":batch,"logical":logical}[sys.argv[1]]()
