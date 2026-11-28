"""Bounded exact-gate Fourier, phase estimation and search workloads."""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector, Pauli as MP
from qcontract import Named, Plan, Pauli, prepare, zero_input


def cs(c,a,b,*,inverse=False):
    # exp(±i*pi*a*b/2) via the parity phase polynomial.
    phase, opposite = ("tdg","t") if inverse else ("t","tdg")
    getattr(c,phase)(a);getattr(c,phase)(b)
    c.cx(a,b);getattr(c,opposite)(b);c.cx(a,b)


def swap(c,a,b):
    c.cx(a,b);c.cx(b,a);c.cx(a,b)


def qft(c,a,b,*,inverse=False,omit_phase=False):
    if inverse:
        swap(c,a,b);c.h(a)
        if not omit_phase:cs(c,a,b,inverse=True)
        c.h(b)
    else:
        c.h(b)
        if not omit_phase:cs(c,a,b)
        c.h(a);swap(c,a,b)


def output(c,labels,expected):
    plan=Plan(tuple(zero_input(label,stabilizes=label) for label in labels))
    p=prepare(c)
    report=plan.verify(p)
    state=Statevector.from_instruction(c)
    numeric=tuple("PASS" if np.isclose(state.expectation_value(MP(label)),1,
                                      rtol=0,atol=1e-12) else "FAIL" for label in labels)
    actual=tuple(r.status for _,r in report.results)
    assert actual==expected==numeric,(labels,actual,expected,numeric)
    return report.explain()


def fourier():
    matrix=np.exp(2j*np.pi*np.outer(np.arange(4),np.arange(4))/4)/2
    f=QuantumCircuit(2);qft(f,0,1)
    assert np.allclose(Operator(f).data,matrix,rtol=0,atol=1e-12)
    rows=[]
    for k in range(4):
        for bad in (False,True):
            c=QuantumCircuit(2)
            for w in range(2):
                if k>>w&1:c.x(w)
            qft(c,0,1,omit_phase=bad)
            # F|k> has X/Y axis on wire 0 and +/-X on wire 1.
            labels=(("IX","IY","-IX","-IY")[k],
                    "-XI" if k&1 else "XI")
            expected=("FAIL","PASS") if bad and k&1 else ("PASS","PASS")
            rows.append({"basis":k,"omitted_phase":bad,"reports":output(c,labels,expected)})
    identity=prepare(QuantumCircuit(2))
    for bad in (False,True):
        c=QuantumCircuit(2);qft(c,0,1);qft(c,0,1,inverse=True,omit_phase=bad)
        p=prepare(c)
        r=p.check(p.equivalent_to(identity,strict=True))
        assert r.status==("FAIL" if bad else "PASS")
        rows.append({"roundtrip":True,"omitted_inverse_phase":bad,"status":r.status})
    return {"cases":rows,"scope":"exact two-wire QFT; no arbitrary rotations"}


def phase_estimation():
    rows=[]
    for k in range(4):
        for bad in (False,True):
            c=QuantumCircuit(3)
            c.x(2);c.h(0);c.h(1)
            # Eigenstate |1> of S**k, controlled powers S**k and S**(2k).
            for _ in range(k):cs(c,0,2)
            if k&1:
                c.h(2);c.cx(1,2);c.h(2)
            qft(c,0,1,inverse=True)
            if bad:c.x(0)
            labels=tuple(("-" if k>>w&1 else "")+("IIZ","IZI")[w] for w in range(2))+("-ZII",)
            expected=("FAIL","PASS","PASS") if bad else ("PASS",)*3
            rows.append({"phase_quarters":k,"readout_fault":bad,"reports":output(c,labels,expected)})
    return {"cases":rows,"scope":"exact grid phases k/4 only"}


def grover():
    rows=[]
    for marked in range(4):
        for bad in (False,True):
            c=QuantumCircuit(2);c.h(0);c.h(1)
            chosen=marked^1 if bad else marked
            for w in range(2):
                if not chosen>>w&1:c.x(w)
            c.h(1);c.cx(0,1);c.h(1)
            for w in range(2):
                if not chosen>>w&1:c.x(w)
            c.h(0);c.h(1);c.x(0);c.x(1)
            c.h(1);c.cx(0,1);c.h(1)
            c.x(0);c.x(1);c.h(0);c.h(1)
            labels=tuple(("-" if marked>>w&1 else "")+("IZ","ZI")[w] for w in range(2))
            rows.append({"marked":marked,"wrong_oracle":bad,
                         "reports":output(c,labels,("FAIL","PASS") if bad else ("PASS",)*2)})
    return {"cases":rows,"scope":"one exact Grover iteration for four items"}


def deutsch_jozsa():
    rows=[]
    for mask in range(4):
        for offset in (0,1):
            c=QuantumCircuit(3);c.x(2)
            for w in range(3):c.h(w)
            if offset:c.x(2)
            for w in range(2):
                if mask>>w&1:c.cx(w,2)
            c.h(0);c.h(1)
            labels=tuple(("-" if mask>>w&1 else "")+("IIZ","IZI")[w] for w in range(2))+("-XII",)
            rows.append({"affine_mask":mask,"offset":offset,
                         "constant":mask==0,"reports":output(c,labels,("PASS",)*3)})
    return {"cases":rows,"scope":"all eight affine functions on two bits; no arbitrary oracle"}
