"""Additional bounded research patterns, not public Ketary APIs."""
import math
from itertools import product
import numpy as np
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit.circuit.library import StatePreparation
from qiskit.quantum_info import Operator
from research import abstraction_primitives as p
from ketary._validation import _int,_angle

def product_state(rows):
    """Each row is (theta,phi); prepare Rz(phi)Ry(theta)|0> on ordered wires."""
    rows=tuple(tuple(_angle(x) for x in p.ordered(row,2)) for row in p.ordered(rows,8))
    if any(len(row)!=2 for row in rows):raise ValueError("expected theta,phi")
    c=q.Circuit(len(rows))
    c.ry([x[0] for x in rows],range(len(rows)))
    return c.rz([x[1] for x in rows],range(len(rows)))

def amplitude_preparation(values):
    """Small native unitary extension, no reset and no assumed dirty-input meaning."""
    raw=p.ordered(values,8)
    if len(raw) not in (2,4,8):raise ValueError("length 2,4,8")
    v=np.asarray(raw,dtype=np.complex128)
    if v.ndim!=1 or not np.isfinite(v).all() or not np.isclose(np.linalg.norm(v),1,atol=1e-12,rtol=0):
        raise ValueError("normalized finite amplitudes required")
    n=int(math.log2(len(v)));native=QuantumCircuit(n)
    native.append(StatePreparation(v),range(n))
    lowered=transpile(native,basis_gates=["u","cx","p","h"],optimization_level=0,
                      seed_transpiler=1101,qubits_initially_zero=False)
    out=q.from_qiskit(lowered)
    if not np.allclose(Operator(native).data,Operator(lowered).data,atol=1e-9,rtol=0):
        raise q.UnsupportedOperation("unitary extension not preserved")
    return out

def _mcx(c,controls,target):
    if len(controls)==1:return c.cx(controls[0],target)
    if len(controls)==2:return c.ccx(*controls,target)
    return c.mcx(controls,target)

def truth_oracle(n,marked):
    """Explicit bit-flip truth table U_f, at most 3 data bits, target wire n."""
    n=p.width(n)
    if n>3:raise q.ResourceLimit("truth table width <=3")
    labels=p.ordered(marked,1<<n,empty=True)
    if any(type(s) is not str or len(s)!=n or set(s)-set("01") for s in labels) or len(set(labels))!=len(labels):
        raise ValueError("expected distinct full-width labels")
    out=q.Circuit(n+1)
    for label in labels:
        zeros=[i for i,b in enumerate(reversed(label)) if b=="0"]
        if zeros:out.x(zeros)
        _mcx(out,list(range(n)),n)
        if zeros:out.x(zeros)
    return out

def amplify(preparation,oracle,iterations):
    """Explicit phase oracle promise; reflect about prepared state."""
    u=p.bound(preparation);o=p.bound(oracle);k=_int(iterations)
    if o.num_qubits!=u.num_qubits:raise ValueError("width mismatch")
    if k>32:raise q.ResourceLimit("iteration cap")
    n=u.num_qubits
    iterate=p.sequence(n,((o,range(n)),(p.reflection(u),range(n))))
    if len(u.to_qiskit().data)+k*len(iterate.to_qiskit().data)>4096:raise q.ResourceLimit("amplification expansion")
    return u.copy() if k==0 else u.copy().apply(iterate,times=k)

def add_register(n):
    """|a>|b> -> |a>|(a+b) mod 2**n>, a in low n wires."""
    n=_int(n,1)
    if n>4:raise q.ResourceLimit("adder <=8 total wires")
    c=q.Circuit(2*n)
    for a in range(n):
        # Add 2**a to b, conditional on the source bit a.
        for j in reversed(range(a,n)):
            controls=[a]+list(range(n+a,n+j))
            _mcx(c,controls,n+j)
    return c

def controlled_power(block,k,controls=1):
    return p.controlled(p.power(block,k),controls)

def conditional_sequence(bit,value,operations):
    """A bounded explicit single-bit condition over supported X/Z operations.

    Returns a dynamic recipe on 3 wires with an explicit measurement of q0.
    No implicit multi-bit predicates or arbitrary native control flow.
    """
    bit=_int(bit);value=_int(value)
    if bit!=0 or value not in (0,1):raise ValueError("fixture uses c0")
    rows=[]
    for raw in p.ordered(operations,16):
        gate,wire=p.ordered(raw,2);wire=_int(wire)
        if gate not in ("x","z") or wire not in (1,2):raise ValueError("supported X/Z on data wires")
        rows.append((gate,wire))
    c=q.Circuit.classical(3,3).x(0).measure(0,0)
    for gate,wire in rows:getattr(c,"if_"+gate)(wire,bit,value=value)
    return c.measure([1,2],[1,2])

def syndrome_phase_flip(error=None):
    """Phase-flip repetition-code syndrome, deterministic computational fixture."""
    c=q.Circuit.classical(5,2).h([0,1,2])
    if error is not None:
        error=_int(error)
        if error>2:raise ValueError("invalid fault")
        c.z(error)
    c.h([0,1,2]).cx(pairs=[(0,3),(1,3),(1,4),(2,4)])
    return c.measure([3,4],[0,1])

def explicit_uncompute_parity(n,controls,ancilla,target):
    """Restricted dependency pattern: compute parity, use it, uncompute.

    Ancilla returns to its input for all basis inputs; desired target XOR
    assumes the ancilla was initially zero. This is not automatic
    uncomputation or a generic ancilla cleanliness proof.
    """
    n=p.width(n);cs=p.wires(controls,n);a,t=_int(ancilla),_int(target)
    if a==t or a in cs or t in cs or max(a,t)>=n:raise ValueError("disjoint roles required")
    compute=p.parity(n,cs,a);action=q.Circuit(n).cx(a,t)
    return p.conjugate(compute,action,n=n,compute_wires=range(n),action_wires=range(n))
