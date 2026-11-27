"""Bounded numerical contracts for Ketary circuits with arbitrary rotations.

A PASS is a numerical agreement, never exact proof. No native admission
extension; Qiskit remains authoritative for mutable circuits.
"""
from dataclasses import dataclass
import math,numpy as np
import ketary
from qiskit.quantum_info import Operator,Statevector,Pauli

@dataclass(frozen=True)
class Numeric:
    status:str
    residual:float
    scope:str

def snapshot(c):
    if not isinstance(c,ketary.Circuit):raise TypeError("Ketary circuit")
    q=c.to_qiskit()
    if not 1<=q.num_qubits<=6 or q.num_clbits or q.num_parameters or len(q.data)>512:raise ValueError("numeric bounds")
    return q

def decide(r,tol,scope):
    if type(tol) not in (int,float) or not math.isfinite(tol) or not 1e-12<=tol<=1e-5 or not math.isfinite(r):raise ValueError("tolerance/residual")
    return Numeric("PASS" if r<=tol/10 else "FAIL" if r>tol*10 else "INCONCLUSIVE",float(r),scope)

def unitary(c,target,*,tol=1e-8):
    q=snapshot(c);d=1<<q.num_qubits
    a=np.asarray(target,dtype=complex)
    if a.shape!=(d,d) or not np.all(np.isfinite(a)) or np.linalg.norm(a.conj().T@a-np.eye(d))>1e-8:raise ValueError("unitary target")
    return decide(float(np.max(np.abs(Operator(q).data-a))),tol,"strict numerical matrix equality")

def probability(c,index,target,*,tol=1e-8):
    q=snapshot(c);d=1<<q.num_qubits
    if type(index) is not int or not 0<=index<d or type(target) not in (int,float) or not math.isfinite(target) or not 0<=target<=1:raise ValueError("probability target")
    v=Statevector.from_instruction(q)
    return decide(abs(float(abs(v.data[index])**2)-target),tol,"zero-input basis probability")

def observable(c,p,target,*,tol=1e-8):
    q=snapshot(c)
    if type(p) is not str or len(p)!=q.num_qubits or any(x not in "IXYZ" for x in p) or type(target) not in (int,float) or not math.isfinite(target) or not -1<=target<=1:raise ValueError("expectation target")
    v=Statevector.from_instruction(q);a=v.expectation_value(Pauli(p))
    return decide(abs(complex(a)-target),tol,"zero-input Pauli expectation")
