"""External QCEC: compare up-to-phase full unitary equivalence only."""
from common5 import *
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import ketary as q
from importlib.metadata import version
def dense(a,b):
    u=Operator(a.to_qiskit()).data;v=Operator(b.to_qiskit()).data
    phase=np.vdot(v,u)/len(u)
    return "PASS" if abs(abs(phase)-1)<1e-9 and np.max(np.abs(u-phase*v))<1e-9 else "FAIL"
def main():
    rows=[]
    for n in (2,4,6,8):
        for kind in ("same","phase","mutant"):
            a=QuantumCircuit(n);a.h(0)
            for i in range(1,n):a.cx(0,i)
            b=a.copy()
            if kind=="phase":b.global_phase=.3
            if kind=="mutant":b.z(0)
            x,y=q.from_qiskit(a),q.from_qiskit(b)
            expected="FAIL" if kind=="mutant" else "PASS";assert dense(x,y)==expected
            def ext():return x.test.external_equivalence(y,deadline=10)
            r=ext()
            assert r["status"]==expected,r
            rows.append({"n":n,"kind":kind,"status":r["status"],"external":r.get("external_equivalence"),"timings":measure({"dense":lambda:dense(x,y),"qcec":ext},reps=3)})
    output({"scope":"full unitary up to global phase, deliberately separated from Pauli contracts; QCEC native relation, no strict-phase claim or proof","qcec":version("mqt.qcec"),"checks":len(rows),"rows":rows})
if __name__=="__main__":main()
