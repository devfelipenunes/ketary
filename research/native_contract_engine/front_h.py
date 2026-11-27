"""H: executable examples of four algorithms; actual Ketary plus research checks."""
from common5 import *
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Statevector
from front_a import numerical,exact

def grover(bad):
    c=QuantumCircuit(2);c.h([0,1])
    if not bad:c.cz(0,1)
    c.h([0,1]);c.x([0,1]);c.cz(0,1);c.x([0,1]);c.h([0,1])
    kc=q.from_qiskit(c);r=kc.run()
    # 2q one marked value and one iteration: exact ideal target probability 1.
    check=q.Contract(2,probabilities={"11":1.}).verify(r)
    return check.status

def qft(bad):
    c=QuantumCircuit(3)
    for j in reversed(range(3)):
        c.h(j)
        for k in reversed(range(j)):c.cp(np.pi/(2**(j-k)),j,k)
    if not bad:c.swap(0,2)
    kc=q.from_qiskit(c);u=Operator(kc.to_qiskit()).data
    x=np.arange(8);ref=np.exp(2j*np.pi*np.outer(x,x)/8)/np.sqrt(8)
    return "PASS" if np.linalg.norm(u-ref,2)<1e-10 else "FAIL"

def adder(bad):
    # 1-bit x, y, clean workspace: compute x into workspace, xor into y, uncompute.
    c=QuantumCircuit(3);c.cx(0,2);c.cx(2,1)
    if not bad:c.cx(0,2)
    kc=q.from_qiskit(c);r=numerical(kc,(2,))
    u=Operator(kc.to_qiskit()).data
    ref=np.zeros((8,4),complex)
    for i in range(4):ref[i^((i&1)<<1),i]=1
    action=np.linalg.norm(u[:,:4]-ref,2)<1e-10
    return "PASS" if r.status=="PASS" and action else "FAIL"

def qec(bad):
    # Coherent three-wire repetition encoding preserves logical Z and maps X.
    c=circuit(3,[(5,0,1),(5,0,2)]+([(4,0,0)] if bad else []));p=prepare(c)
    # On full domain U† XXX U = X0, U† Z0 U = Z0.
    rs=verify(p,(Obligation((1,0,0),(7,0,0)),Obligation((0,1,0),(0,1,0))))
    return "PASS" if all(r.status=="PASS" for r in rs) else "FAIL"

def main():
    rows=[]
    for name,f in (("grover_snapshot",grover),("qft_strict_operator",qft),("reversible_adder_subspace",adder),("repetition_encoding_logical_paulis",qec)):
        for bad in (False,True):
            status=f(bad);assert status==("FAIL" if bad else "PASS"),(name,bad,status)
            rows.append({"algorithm":name,"mutant":bad,"status":status,"timings":measure({"build_verify":lambda:f(bad)})})
    output({"scope":"worked examples, actual Ketary; QFT and adder are research numeric oracles, encoding is not full error correction; no human usability evidence","checks":len(rows),"rows":rows})
if __name__=="__main__":main()
