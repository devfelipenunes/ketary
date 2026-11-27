"""D: maximum leakage on an admitted clean subspace, restricted columns vs full operator."""
from common5 import *
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator,Statevector
import ketary as q
from front_a import wires_ok

def check(c,w,method,*,tol=1e-9):
    qc=c.to_qiskit();n=qc.num_qubits;mask=wires_ok(n,w)
    if method not in ("columns","operator") or not 0<tol<=1e-6:raise ValueError("policy")
    if not 1<=n<=12 or n-len(w)>4 or len(qc.data)>256 or qc.num_parameters or qc.num_clbits or (method=="operator" and n>8):return ("UNSUPPORTED",None,None,None)
    # Ketary Circuit is an admitted bound unitary logical circuit.
    clean=np.array([i for i in range(1<<n) if not i&mask],dtype=np.int64)
    dirty=np.array([i for i in range(1<<n) if i&mask],dtype=np.int64)
    if method=="operator":
        u=Operator(qc).data;columns=u[:,clean].copy()
    else:
        columns=np.empty((1<<n,len(clean)),complex)
        for j,i in enumerate(clean):
            columns[:,j]=Statevector.from_int(int(i),2**n).evolve(qc).data
    if not np.isfinite(columns).all() or np.linalg.norm(columns.conj().T@columns-np.eye(len(clean)),2)>1e-10:raise ValueError("isometry")
    _,s,vh=np.linalg.svd(columns[dirty,:],full_matrices=False);p=float(s[0]**2)
    # Reproduce a valid input witness by fresh native evolution, not SVD data.
    v=np.zeros(1<<n,complex);v[clean]=vh[0].conj()
    out=Statevector(v).evolve(qc).data;gap=float(np.linalg.norm(out[dirty])**2)
    if abs(p-gap)>1e-10:raise ArithmeticError("witness")
    status="PASS" if p<tol-1e-12 else "FAIL" if p>tol+1e-12 and gap>tol+1e-12 else "INCONCLUSIVE"
    return status,p,gap,v if status=="FAIL" else None

def fixture(n,k,kind):
    # Data qubits 0..k-1; others clean. Coherent failure: H then CNOT
    # leaks with maximum 1 even though each classical input leaks only 1/2.
    c=QuantumCircuit(n)
    for i in range(k):c.h(i)
    for j in range(k,n):
        c.cx(j%k,j);c.z(j);c.cx(j%k,j)
    if kind=="dirty":c.cx(0,k)
    if kind=="boundary":c.ry(2*np.arcsin(np.sqrt(1e-9)),k)
    if kind=="tiny":c.ry(2*np.arcsin(np.sqrt(1e-12)),k)
    return q.from_qiskit(c),tuple(range(k,n))

def main():
    rows=[];matched=0;checks=0
    for n in (4,6,8,10,12):
        for k in (1,2,4):
            if k>=n:continue
            for kind in ("clean","dirty","boundary","tiny"):
                c,w=fixture(n,k,kind)
                r=check(c,w,"columns");expected={"clean":"PASS","dirty":"FAIL","boundary":"INCONCLUSIVE","tiny":"PASS"}[kind]
                assert r[0]==expected and abs(r[1]-{"clean":0.,"dirty":1.,"boundary":1e-9,"tiny":1e-12}[kind])<1e-10
                checks+=1
                if n<=8:
                    ref=check(c,w,"operator");assert ref[0]==r[0] and abs(ref[1]-r[1])<1e-10;matched+=1
                else:assert check(c,w,"operator")[0]=="UNSUPPORTED"
                if kind not in ("clean","dirty"):continue
                fs={"restricted":lambda:check(c,w,"columns")}
                if n<=8:fs["operator"]=lambda:check(c,w,"operator")
                rows.append({"n":n,"data":k,"ancillas":len(w),"kind":kind,"operator_payload_bytes":16*4**n,"columns_payload_bytes":16*2**(n+k),"timings":measure(fs,reps=5)})
    output({"scope":"numeric maximum leakage probability on entire clean input subspace; trusted Ketary logical gates, matched column/Operator metric, independent witness; payload only not RSS; no certified roundoff","checks":checks,"matched_checks":matched,"rows":rows})
if __name__=="__main__":main()
