"""Reversible arithmetic, ideal random-bit preparation and distance-three QEC."""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector, Pauli as MP
from qcontract import Correctable, Named, Pauli, Plan, ZBranch, prepare, zero_input

HALF=((1,0),1)
ZERO=((0,0),0)


def toffoli(c,a,b,t):
    # Exact Clifford+T CCX, not a relative-phase Toffoli.
    c.h(t);c.cx(b,t);c.tdg(t);c.cx(a,t);c.t(t)
    c.cx(b,t);c.tdg(t);c.cx(a,t);c.t(b);c.t(t);c.h(t)
    c.cx(a,b);c.t(a);c.tdg(b);c.cx(a,b)


def basis_claim(c,index,expected):
    n=c.num_qubits
    labels=tuple(("-" if index>>w&1 else "")+"I"*(n-w-1)+"Z"+"I"*w for w in range(n))
    plan=Plan(tuple(zero_input(label,stabilizes=label) for label in labels))
    p=prepare(c);r=plan.verify(p);v=Statevector.from_instruction(c)
    oracle=tuple("PASS" if np.isclose(v.expectation_value(MP(label)),1,
                                     rtol=0,atol=1e-12) else "FAIL" for label in labels)
    actual=tuple(x.status for _,x in r.results)
    assert actual==expected==oracle,(index,actual,expected,oracle)
    return r.explain()


def half_adder():
    rows=[]
    for bad in (False,True):
        operation=QuantumCircuit(4)
        operation.cx(0,2);operation.cx(1,2)
        if not bad:toffoli(operation,0,1,3)
        target=np.zeros((16,4),complex)
        for k in range(4):
            a,b=k&1,k>>1
            want=k|((a^b)<<2)|((a&b)<<3)
            target[want,k]=1
            c=QuantumCircuit(4)
            for w in range(2):
                if k>>w&1:c.x(w)
            c.compose(operation,inplace=True)
            expected=("PASS","PASS","PASS","FAIL") if bad and k==3 else ("PASS",)*4
            rows.append({"input":k,"missing_carry":bad,"reports":basis_claim(c,want,expected)})
        # Independent check on the entire clean-input isometry, not merely
        # the output populations; this numerical check is not an exact contract.
        assert bool(np.allclose(Operator(operation).data[:,:4],target,rtol=0,atol=1e-12)) == (not bad)
    return {"cases":rows,"scope":"four classical input contracts plus independent numeric isometry"}


def incrementer():
    rows=[]
    target=np.zeros((8,8),complex)
    for k in range(8):target[(k+1)%8,k]=1
    for bad in (False,True):
        operation=QuantumCircuit(3)
        if not bad:toffoli(operation,0,1,2)
        operation.cx(0,1);operation.x(0)
        assert bool(np.allclose(Operator(operation).data,target,rtol=0,atol=1e-12))==(not bad)
        for k in range(8):
            c=QuantumCircuit(3)
            for w in range(3):
                if k>>w&1:c.x(w)
            c.compose(operation,inplace=True)
            expected=("PASS","PASS","FAIL") if bad and k%4==3 else ("PASS",)*3
            rows.append({"input":k,"missing_high_carry":bad,
                         "reports":basis_claim(c,(k+1)%8,expected)})
    return {"cases":rows,"scope":"modular increment on all eight basis inputs; numeric full operator check"}


def random_bit_preparation():
    rows=[]
    for name in ("independent","biased","correlated"):
        c=QuantumCircuit(2)
        if name!="biased":c.h(0)
        if name=="correlated":c.cx(0,1)
        else:c.h(1)
        p=prepare(c);v=Statevector.from_instruction(c).data
        for branch in (0,1):
            spec=ZBranch(0,branch,Pauli("ZI"),HALF,ZERO)
            result=p.check(spec)
            probability=sum(abs(a)**2 for i,a in enumerate(v) if i&1==branch)
            moment=sum(abs(a)**2*(1 if not i&2 else -1) for i,a in enumerate(v) if i&1==branch)
            oracle="PASS" if np.allclose((probability,moment),(0.5,0),rtol=0,atol=1e-12) else "FAIL"
            expected="PASS" if name=="independent" else "FAIL"
            assert result.status==expected==oracle
            rows.append({"case":name,"branch":branch,"probability":float(probability),
                         "unnormalized_moment":float(moment),"status":result.status})
    return {"cases":rows,"scope":"ideal computational-basis distribution; no entropy or device certification"}


def five_qubit_code():
    stabilizers=("XZZXI","IXZZX","XIXZZ","ZXIXZ")
    projector=np.eye(32,dtype=complex)
    for s in stabilizers:projector=projector@(np.eye(32)+MP(s).to_matrix())/2
    eigenvalues,eigenvectors=np.linalg.eigh(projector)
    basis=eigenvectors[:,eigenvalues>0.5]
    assert basis.shape==(32,2)
    single=("IIIII",)+tuple("I"*w+p+"I"*(4-w) for w in range(5) for p in "XYZ")
    rows=[]
    for name,errors,expected in (("all single Pauli errors",single,"PASS"),
                                  ("added logical operator",single+("XXXXX",),"FAIL"),
                                  ("added conflicting double error",single+("IYYII",),"FAIL")):
        spec=Correctable(tuple(Pauli(s) for s in stabilizers),tuple(Pauli(e) for e in errors))
        p=prepare(QuantumCircuit(5))
        result=p.check(spec)
        matrices=[MP(e).to_matrix() for e in errors]
        violations=[]
        for i,a in enumerate(matrices):
            for j,b in enumerate(matrices[i:],i):
                m=basis.conj().T@a.conj().T@b@basis
                if not np.allclose(m,np.trace(m)*np.eye(2)/2,rtol=0,atol=1e-12):
                    violations.append([errors[i],errors[j]])
        assert result.status==expected==("FAIL" if violations else "PASS"),(name,result.status,violations)
        assert result.snapshots==()
        rows.append({"case":name,"errors":len(errors),"status":result.status,
                     "violating_pairs":violations,"obligation":result.obligation})
    return {"cases":rows,"scope":"finite [[5,1,3]] code criterion, no recovery implementation"}
