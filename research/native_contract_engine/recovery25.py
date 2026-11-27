"""Ideal coherent syndrome extraction, finite Pauli recovery and circuit contracts.

Qiskit circuit construction is separate from exact admission and dense validation.
No noisy device, fault-tolerance or measurement hardware claim.
"""
from qiskit import QuantumCircuit
from independent20 import pauli,correctable_pauli_set,anticommute
from structures21 import recovery_table,correction

def extraction(n,stabilizers):
    # Validation: independent commuting generators, no identity.
    r=correctable_pauli_set(n,stabilizers,((0,0,0),))
    if r.status!="PASS" or n+len(stabilizers)>14:raise ValueError("extraction bounds")
    q=QuantumCircuit(n+len(stabilizers),name="syndrome-extraction")
    for j,(x,z,s) in enumerate(stabilizers):
        a=n+j;q.h(a)
        for i in range(n):
            u,v=(x>>i)&1,(z>>i)&1
            if u and v:q.cy(a,i)
            elif u:q.cx(a,i)
            elif v:q.cz(a,i)
        if s:q.z(a)
        q.h(a)
    return q

def apply_pauli(q,p,n):
    x,z,s=pauli(n,p)
    for i in range(n):
        u,v=(x>>i)&1,(z>>i)&1
        if u and v:q.y(i)
        elif u:q.x(i)
        elif v:q.z(i)
    if s:q.global_phase+=3.141592653589793

def recovery_circuit(n,stabilizers,errors):
    t=recovery_table(n,stabilizers,errors)
    if t.status!="PASS" or n+len(stabilizers)>14:return None
    # Explicit measurement and classical correction. No Aer dependency is
    # required to construct the circuit. The exact syndrome and conditional
    # data action are tested separately on ideal state vectors.
    m=len(stabilizers);q=QuantumCircuit(n+m,m)
    q.compose(extraction(n,stabilizers),inplace=True)
    q.measure(range(n,n+m),range(m))
    for key,p in t.table:
        if p[:2]==(0,0):continue
        with q.if_test((q.cregs[0],sum(b<<i for i,b in enumerate(key)))):
            apply_pauli(q,(p[0],p[1],0),n)
    return q
