"""A: joint clean-ancilla subspace, exact Clifford and numeric leakage."""
from dataclasses import dataclass
import random
import numpy as np
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Pauli
from common5 import *
from benchmark import py
from test_engine import witness_state
from engine import Witness

@dataclass(frozen=True)
class SubspaceReport:
    status:str
    method:str
    wires:tuple
    metric:str
    leakage:float|None
    witness:tuple|None

def wires_ok(n,w):
    if type(w) is not tuple or not w or len(w)>n or any(type(i) is not int or not 0<=i<n for i in w) or len(set(w))!=len(w):raise ValueError("ancilla wires")
    return sum(1<<i for i in w)

def exact(pre,w):
    admission(pre);mask=wires_ok(pre.width,w)
    if any(op>=6 for op,_,_ in pre.gates):return SubspaceReport("UNSUPPORTED","clifford",w,"exact zero leakage",None,None)
    for wire in w:
        x,z,r=py(pre.gates,pre.width,(0,1<<wire,0))
        # A signed Pauli stabilizes every input in the joint +1 subspace
        # iff it is a positive product of the ancilla Z generators.
        if not x and not z&~mask and r==0:continue
        axes=["Z"]*pre.width;signs=[1]*pre.width
        if not x&mask:
            support=(x|z)&~mask
            for i in range(pre.width):
                if support&(1<<i):
                    axes[i]="IZXY"[2*((x>>i)&1)+((z>>i)&1)]
            if support and r==0:signs[(support&-support).bit_length()-1]=-1
        # X/Y on any ancilla => expectation zero; otherwise -1 chosen.
        return SubspaceReport("FAIL","clifford",w,"exact zero leakage",None,(tuple(axes),tuple(signs)))
    return SubspaceReport("PASS","clifford",w,"exact zero leakage",0.,None)

def numerical(c,w,tol=1e-9):
    qc=c.to_qiskit();n=qc.num_qubits;mask=wires_ok(n,w)
    if type(tol) not in (int,float) or not np.isfinite(tol) or not 0<=tol<=1e-6:raise ValueError("tolerance")
    if not 1<=n<=6 or len(qc.data)>256 or qc.num_parameters or qc.num_clbits:return SubspaceReport("UNSUPPORTED","svd",w,"maximum leakage probability",None,None)
    u=Operator(qc).data
    if not np.isfinite(u).all() or np.linalg.norm(u.conj().T@u-np.eye(len(u)),2)>1e-12:raise ValueError("unitary admission")
    clean=[i for i in range(len(u)) if not i&mask];dirty=[i for i in range(len(u)) if i&mask]
    _,s,vh=np.linalg.svd(u[np.ix_(dirty,clean)],full_matrices=False)
    v=np.zeros(len(u),complex);v[clean]=vh[0].conj();leak=float(s[0]**2);gap=float(np.linalg.norm((u@v)[dirty])**2)
    if abs(leak-gap)>1e-10:raise ArithmeticError("witness reproduction")
    status="PASS" if leak<tol-1e-12 else "FAIL" if leak>tol+1e-12 and gap>tol+1e-12 else "INCONCLUSIVE"
    return SubspaceReport(status,"svd",w,"maximum leakage probability",leak,tuple((float(z.real),float(z.imag)) for z in v) if status=="FAIL" else None)

def main():
    rng=random.Random(61);checks=0;fails=0;rows=[]
    for n in (2,3,4,5):
        for j in range(24):
            w=tuple(rng.sample(range(n),rng.randrange(1,n+1)))
            c=circuit(n,gates(n,18,j));p=prepare(c)
            r=exact(p,w);s=numerical(c,w)
            assert r.status==s.status;checks+=1
            if r.status=="FAIL":
                axes,signs=r.witness;v=witness_state(Witness(axes,signs,(0,0),0))
                u=Operator(c.to_qiskit()).data;mask=wires_ok(n,w);dirty=[i for i in range(len(u)) if i&mask]
                assert np.linalg.norm(v[dirty])<1e-10 and np.linalg.norm((u@v)[dirty])**2>=.5-1e-10;fails+=1
    # Swapping two clean ancillas preserves their joint space.
    c=circuit(3,[(5,1,2),(5,2,1),(5,1,2)])
    assert exact(prepare(c),(1,2)).status=="PASS"
    assert exact(prepare(c),(1,)).status=="FAIL"
    assert numerical(c,(1,2)).status=="PASS"
    for n in (3,5,6):
        for w in ((0,),(0,n-1)):
            for prob in (0.,1e-9,.25):
                qc=QuantumCircuit(n);qc.ry(2*np.arcsin(np.sqrt(prob)),w[0]);c=q.from_qiskit(qc)
                r=numerical(c,w);assert r.status=={0.:"PASS",1e-9:"INCONCLUSIVE",.25:"FAIL"}[prob];assert abs(r.leakage-prob)<1e-10
                rows.append({"n":n,"wires":w,"prob":prob,"status":r.status,"timings":measure({"numeric_full":lambda:numerical(c,w)})})
    output({"scope":"joint zero subspace; exact Clifford vs bounded numeric leakage with independent domain witness; distinct guarantees","random_checks":checks,"exact_witness_checks":fails,"boundary_checks":len(rows),"swap_controls":3,"rows":rows})
if __name__=="__main__":main()
