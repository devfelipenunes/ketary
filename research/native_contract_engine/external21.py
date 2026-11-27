"""Matched external benchmark: signed Clifford images; phase-insensitive QCEC.
External dependencies belong only to the research CI environment."""
import json,random,importlib.metadata as md
import stim
from mqt import qcec
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford,Pauli,Operator
import numpy as np
from common5 import circuit,measure
from benchmark import label
from native9 import RustSession
from planner19 import plan_transition

def pack(gs):return bytes(v for g in gs for v in g)
def stim_pauli(n,p):
    return stim.PauliString(("-" if p[2] else "+")+label(n,(*p[:2],0))[::-1].replace("I","_"))
def cliff():
    rng=random.Random(2121);rows=[]
    for n in (4,16,32,64):
        gs=[]
        for _ in range(256):
            a,b=rng.sample(range(n),2);op=rng.randrange(6);gs.append((op,a,b if op==5 else 0))
        q=circuit(n,gs).to_qiskit();s=RustSession(n,pack(gs))
        st=stim.Circuit()
        for op,a,b in gs:st.append(("H","S","S_DAG","X","Z","CX")[op],[a,b] if op==5 else [a])
        t=stim.Tableau.from_circuit(st).inverse();cl=Clifford(q)
        p=(rng.getrandbits(n),rng.getrandbits(n),0);sp=stim_pauli(n,p);qp=Pauli(label(n,p))
        r=s.propagate(p);x,z,c,b=r.terms[0];pre=x,z,int(c<0)
        assert r.denominator_power==0 and b==0 and abs(c)==1
        assert t(sp)==stim_pauli(n,pre) and qp.evolve(cl,frame="h")==Pauli(label(n,pre))
        rows.append({"n":n,"gates":len(gs),"timings":measure({"rust":lambda:s.propagate(p),"stim":lambda:t(sp),"qiskit":lambda:qp.evolve(cl,frame="h")},reps=21)})
    return rows
def equivalence():
    rows=[]
    for n in (2,3,4,5):
        q=QuantumCircuit(n);q.h(0);q.cx(0,1);q.t(1);q.tdg(1);q.cx(0,1)
        a=q.copy();b=QuantumCircuit(n);b.h(0)
        for mutate in (False,True):
            test=b.copy()
            if mutate:test.x(1)
            u,v=Operator(a),Operator(test)
            expected=u.equiv(v)
            # QCEC checks full unitary equivalence (global phase allowed);
            # compare with native all-generator equivalence on same scope.
            from consolidated12 import Engine
            import ketary as k
            ae,be=Engine.prepare(k.from_qiskit(a)),Engine.prepare(k.from_qiskit(test))
            native=ae.equivalent(be)
            assert native.status==("PASS" if expected else "FAIL")
            def external():return qcec.verify(a,test)
            result=external()
            status=str(result.equivalence).split(".")[-1]
            # Do not coerce probable equivalence or timeouts into proof.
            definite=status in ("equivalent","equivalent_up_to_global_phase","not_equivalent")
            if definite:assert (status!="not_equivalent")==expected
            rows.append({"n":n,"mutant":mutate,"expected":expected,"qcec_status":status,"native_status":native.status,"timings":measure({"native":lambda:ae.equivalent(be),"qcec":external,"dense":lambda:u.equiv(v)},reps=7)})
    return rows
if __name__=="__main__":
    print(json.dumps({"scope":"prebuilt signed Clifford conjugation, separate full unitary equivalence modulo phase pilot; setup not included in Clifford timings; QCEC verify includes setup","versions":{p:md.version(p) for p in ("stim","mqt.qcec","qiskit")},"clifford":cliff(),"equivalence":equivalence()},indent=2))
