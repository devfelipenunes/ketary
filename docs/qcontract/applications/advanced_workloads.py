"""Six additional bounded algorithmic decisions."""
import math
import pathlib
import runpy

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector, Pauli as MP
from qcontract import Named, Pauli, Plan, ZBranch, prepare, transition, zero_input

ROOT=pathlib.Path(__file__).resolve().parent
ARITH=runpy.run_path(str(ROOT/"arithmetic_and_qec.py"))
toffoli=ARITH["toffoli"]
basis_claim=ARITH["basis_claim"]
HALF=((1,0),1)
ZERO=((0,0),0)


def fredkin(c,control,a,b):
    c.cx(a,b);toffoli(c,control,b,a);c.cx(a,b)


def period_finding():
    # One-bit phase estimation of order-two multiplication by 4 mod 15.
    # Bit rotation by two on the 4-wire work register realizes this
    # permutation, with 15 fixed. This is NOT general Shor factoring.
    rows=[]
    for bad in (False,True):
        c=QuantumCircuit(5);c.x(1);c.h(0)
        if not bad:fredkin(c,0,1,3)
        fredkin(c,0,2,4)
        c.h(0)
        p=prepare(c);v=Statevector.from_instruction(c).data
        for branch in (0,1):
            spec=ZBranch(0,branch,Pauli("IIIZI"),HALF,ZERO)
            result=p.check(spec)
            prob=sum(abs(a)**2 for i,a in enumerate(v) if i&1==branch)
            moment=sum(abs(a)**2*(1 if not i&2 else -1)
                       for i,a in enumerate(v) if i&1==branch)
            numeric="PASS" if np.allclose((prob,moment),(0.5,0),rtol=0,atol=1e-12) else "FAIL"
            assert result.status==numeric==("FAIL" if bad else "PASS")
            rows.append({"omitted_swap":bad,"phase_bit":branch,
                         "probability":float(prob),"status":result.status})
    assert pow(4,2,15)==1 and 4%15!=1
    factors=[math.gcd(4-1,15),math.gcd(4+1,15)]
    assert factors==[3,5]
    return {"cases":rows,"classical_order_check":2,"classical_factors":factors,
            "scope":"order-two instance; no general modular exponentiation or factoring advantage"}


def quantum_walk():
    rows=[]
    labels=("-IIZ","ZZI","XXI")
    plan=Plan(tuple(zero_input(label,stabilizes=label) for label in labels))
    for bad in (False,True):
        c=QuantumCircuit(3);c.h(2)
        c.cx(0,1)
        if not bad:c.cx(2,1)
        c.x(0)
        p=prepare(c);outcome=plan.verify(p)
        v=Statevector.from_instruction(c).data
        expected=("PASS","FAIL","FAIL") if bad else ("PASS",)*3
        numeric=tuple("PASS" if np.isclose(
            np.vdot(v,MP(label).to_matrix()@v),1,rtol=0,atol=1e-12)
                      else "FAIL" for label in labels)
        assert tuple(r.status for _,r in outcome.results)==expected==numeric
        if not bad:
            target=np.zeros(8,complex);target[1]=target[7]=1/np.sqrt(2)
            assert np.allclose(v,target,rtol=0,atol=1e-12)
        rows.append({"direction_fault":bad,"reports":outcome.explain()})
    return {"cases":rows,"scope":"one coined walk step on a four-cycle from position zero"}


def phase_kickback():
    rows=[]
    for bad in (False,True):
        c=QuantumCircuit(2);c.cx(0,1)
        # An initially minus eigenstate on the target yields Z on control.
        prep=QuantumCircuit(2);prep.x(1);prep.h(1)
        prep.compose(c,inplace=True)
        ref=QuantumCircuit(2);ref.x(1);ref.h(1);ref.z(0)
        if bad:prep.x(0)
        p=prepare(prep);q=prepare(ref)
        claim=Named("Logical phase on clean input",p.action_matches(q,ancillas=(1,)))
        r=Plan((claim,)).verify(p)
        a,b=Operator(prep).data[:,:2],Operator(ref).data[:,:2]
        phase=np.vdot(b,a)/2
        numeric="PASS" if np.isclose(abs(phase),1,rtol=0,atol=1e-12) and np.allclose(
            a,phase*b,rtol=0,atol=1e-12) else "FAIL"
        assert r.results[0][1].status==numeric==("FAIL" if bad else "PASS")
        rows.append({"logical_bit_fault":bad,"reports":r.explain()})
    return {"cases":rows,"scope":"arbitrary logical input, initial clean workspace prepared in minus eigenstate"}


def syndrome_readout():
    # Coherent parity syndrome for one Z stabilizer of bit repetition.
    rows=[]
    for error in (None,0,1,2):
        c=QuantumCircuit(4);c.h(0);c.cx(0,1);c.cx(0,2)
        if error is not None:c.x(error)
        c.cx(0,3);c.cx(1,3)
        syndrome=error in (0,1)
        labels=("-ZIII" if syndrome else "ZIII",)
        p=prepare(c);outcome=Plan((zero_input("Expected parity syndrome",
                                             stabilizes=labels[0]),)).verify(p)
        v=Statevector.from_instruction(c).data
        assert outcome.passed and np.isclose(np.vdot(v,MP(labels[0]).to_matrix()@v),
                                             1,rtol=0,atol=1e-12)
        # Incorrect opposite claim must fail, regardless of error class.
        opposite="ZIII" if syndrome else "-ZIII"
        assert not Plan((zero_input("Wrong syndrome",stabilizes=opposite),)).verify(p).passed
        rows.append({"bit_error_wire":error,"expected_syndrome":int(syndrome),
                     "reports":outcome.explain()})
    return {"cases":rows,"scope":"ideal coherent extraction of one stabilizer; not full recovery"}


def conditional_router():
    rows=[]
    for bad in (False,True):
        c=QuantumCircuit(3)
        if not bad:fredkin(c,0,1,2)
        p=prepare(c);matrix=Operator(c).data
        target=np.zeros((8,8),complex)
        for k in range(8):
            a,b=(k>>1)&1,(k>>2)&1
            want=(k&1)|((b if k&1 else a)<<1)|((a if k&1 else b)<<2)
            target[want,k]=1
        assert bool(np.allclose(matrix,target,rtol=0,atol=1e-12))==(not bad)
        # Control and total ZZ parity are genuine all-input invariants,
        # but alone they do not prove the controlled routing action.
        plan=Plan((transition("Preserve control",before="IIZ",after="IIZ"),
                   transition("Preserve data parity",before="ZZI",after="ZZI")))
        assert plan.verify(p).passed
        for k in range(8):
            a,b=(k>>1)&1,(k>>2)&1
            want=(k&1)|((b if k&1 else a)<<1)|((a if k&1 else b)<<2)
            expected=("PASS","FAIL","FAIL") if bad and k&1 and a!=b else ("PASS",)*3
            source=QuantumCircuit(3)
            for w in range(3):
                if k>>w&1:source.x(w)
            source.compose(c,inplace=True)
            rows.append({"input":k,"missing_router":bad,
                         "reports":basis_claim(source,want,expected)})
    return {"cases":rows,"scope":"all basis inputs and independent numeric operator; invariants alone insufficient"}


def reversible_comparator():
    rows=[]
    for bad in (False,True):
        operation=QuantumCircuit(3)
        if not bad:operation.x(1)
        toffoli(operation,0,1,2)
        if not bad:operation.x(1)
        for k in range(4):
            c=QuantumCircuit(3)
            for w in range(2):
                if k>>w&1:c.x(w)
            c.compose(operation,inplace=True)
            a,b=k&1,k>>1
            target=k|(int(a>b)<<2)
            expected=("PASS","PASS","FAIL") if bad and a else ("PASS",)*3
            rows.append({"input":k,"wrong_predicate":bad,
                         "reports":basis_claim(c,target,expected)})
    return {"cases":rows,"scope":"one-bit unsigned comparison, preserved data and output flag"}
