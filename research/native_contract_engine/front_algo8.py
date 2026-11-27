"""Algorithm workloads: GHZ preparation inverse, parity oracle and reversible Toffoli."""
from common5 import *
from front_d7 import check
from qiskit import QuantumCircuit
import ketary as q
from engine import verify
def main():
    rows=[]
    for n in (8,16,32,64):
        for bad in (False,True):
            gs=[(0,0,0)]+[(5,0,i) for i in range(1,n)]
            # U maps Z0 to X on all wires in the forward direction.
            if bad:gs.append((4,0,0))
            p=prepare(circuit(n,gs));ob=Obligation((0,1,0),((1<<n)-1,0,0))
            r=verify(p,(ob,))[0];assert r.status==("FAIL" if bad else "PASS")
            rows.append({"algorithm":"GHZ logical Pauli","n":n,"mutant":bad,"status":r.status,"timings":measure({"report":lambda:verify(p,(ob,))})})
    for n in (5,8,10,12):
        for bad in (False,True):
            qc=QuantumCircuit(n);qc.ccx(0,1,2);qc.cx(2,3)
            if not bad:qc.ccx(0,1,2)
            # Data 0,1,3; ancilla 2 and all other wires.
            c=q.from_qiskit(qc);w=(2,)+tuple(range(4,n))
            r=check(c,w,"columns");assert r[0]==("FAIL" if bad else "PASS")
            rows.append({"algorithm":"Toffoli compute-action-uncompute clean ancilla","n":n,"mutant":bad,"status":r[0],"timings":measure({"report":lambda:check(c,w,"columns")})})
    output({"scope":"algorithm components with deliberate mutants; GHZ Pauli transition and reversible workspace only, not full algorithm correctness or human study","checks":len(rows),"rows":rows})
if __name__=="__main__":main()
