"""Research-only compositional experiments. Not installed or public API.

All outputs are ordinary Ketary Circuits; construction never executes a
statevector. Use bounded, explicit input rows, with no automatic ancillas,
cache, second IR, or implicit approximation.
"""
from collections.abc import Mapping
from itertools import islice
from math import pi
import numpy as np
import ketary as q
from ketary._validation import _int, _angle
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator

def ordered(items, cap, *, empty=False):
    if isinstance(items,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected ordered iterable")
    try:
        rows=tuple(islice(iter(items),cap+1))
    except TypeError as exc:
        raise ValueError("expected ordered iterable") from exc
    if len(rows)>cap:
        raise q.ResourceLimit("research input cap exceeded")
    if not rows and not empty:
        raise ValueError("empty input")
    return rows

def width(n):
    n=_int(n,1)
    if n>8:raise q.ResourceLimit("research operator width <=8")
    return n

def wires(items,n,arity=None):
    row=tuple(_int(w) for w in ordered(items,n))
    if (arity is not None and len(row)!=arity) or len(set(row))!=len(row) or max(row)>=n:
        raise ValueError("invalid ordered wires")
    return row

def bound(c):
    if not isinstance(c,q.Circuit):raise TypeError("expected Circuit")
    width(c.num_qubits)
    if c.num_clbits or c.parameters:raise q.UnsupportedOperation("bound unitary only")
    if len(c.to_qiskit().data)>4096:raise q.ResourceLimit("research block cap")
    return c

def aligned(c,gate,angles,pairs):
    """Independent candidate for existing pairs= overload, including symbols."""
    if not isinstance(c,q.Circuit):raise TypeError("expected Circuit")
    width(c.num_qubits)
    if gate not in ("cp","crx","cry","crz","rxx","ryy","rzz"):
        raise ValueError("unsupported two-wire rotation")
    p=tuple(wires(row,c.num_qubits,2) for row in ordered(pairs,256))
    a=ordered(angles,len(p))
    if len(a)!=len(p):raise ValueError("one angle per pair")
    # Existing scalar methods validate the mode and parameter identity.
    # Private output staging means a late error never changes the input.
    out=c.copy()
    for theta,(i,j) in zip(a,p,strict=True):
        getattr(out,gate)(theta,i,j)
    return out

def sequence(n,placements):
    n=width(n)
    entries=[]
    total=0
    for row in ordered(placements,256,empty=True):
        block,where=ordered(row,2)
        block=bound(block)
        total+=len(block.to_qiskit().data)
        if total>4096:raise q.ResourceLimit("sequence expansion")
        entries.append((block,wires(where,n,block.num_qubits)))
    out=q.Circuit(n)
    for block,where in entries:out.apply(block,wires=where)
    return out

def layers(template,rows):
    """Sequential layers, not SweepPlan's independent executions."""
    if not isinstance(template,q.Circuit) or template.num_clbits:
        raise TypeError("expected symbolic unitary template")
    n=width(template.num_qubits)
    if not 1<=len(template.parameters)<=32:raise ValueError("expected symbolic parameters")
    values=tuple(tuple(_angle(v) for v in ordered(row,len(template.parameters))) for row in ordered(rows,32))
    if any(len(row)!=len(template.parameters) for row in values):raise ValueError("wrong row width")
    if len(template.to_qiskit().data)*len(values)>4096:raise q.ResourceLimit("layer expansion")
    return sequence(n,((template.bind(row),range(n)) for row in values))

def power(c,k):
    c=bound(c)
    if isinstance(k,bool):raise ValueError("invalid power")
    import operator
    k=operator.index(k)
    if abs(k)>64 or abs(k)*len(c.to_qiskit().data)>4096:
        raise q.ResourceLimit("power expansion")
    if k==0:return q.Circuit(c.num_qubits)
    return (c if k>0 else c.inverse()).repeat(abs(k))

def conjugate(compute,action,*,n,compute_wires,action_wires):
    n=width(n);compute=bound(compute);action=bound(action)
    cw=wires(compute_wires,n,compute.num_qubits);aw=wires(action_wires,n,action.num_qubits)
    return sequence(n,((compute,cw),(action,aw),(compute.inverse(),cw)))

def _terms(H,n):
    if not isinstance(H,q.Observable):raise TypeError("expected real Observable")
    return tuple((label,coef) for label,coef in H.to_dict(n).items() if coef!=0)

def _commute(a,b):
    return sum(x!="I" and y!="I" and x!=y for x,y in zip(a,b,strict=True))%2==0

def pauli_rotation(label,theta):
    """exp(-i*theta*P/2), including the all-identity global phase."""
    if type(label) is not str or not label or set(label)-set("IXYZ"):raise ValueError("invalid Pauli")
    n=width(len(label));theta=_angle(theta)
    native=QuantumCircuit(n)
    active=[(i,p) for i,p in enumerate(reversed(label)) if p!="I"]
    if not active:
        native.global_phase=-theta/2
        return q.from_qiskit(native)
    for i,p in active:
        if p=="X":native.h(i)
        elif p=="Y":native.sdg(i);native.h(i)
    target=active[-1][0]
    for i,_ in active[:-1]:native.cx(i,target)
    native.rz(theta,target)
    for i,_ in reversed(active[:-1]):native.cx(i,target)
    for i,p in reversed(active):
        if p=="X":native.h(i)
        elif p=="Y":native.h(i);native.s(i)
    return q.from_qiskit(native)

def evolve(H,time,*,n=None):
    """Exact commuting evolution in algebraic semantics, numerical gates."""
    if not isinstance(H,q.Observable):raise TypeError("expected Observable")
    n=width(H.num_qubits if n is None else n);t=_angle(time)
    terms=_terms(H,n)
    if any(not _commute(a,b) for i,(a,_) in enumerate(terms) for b,_ in terms[i+1:]):
        raise q.UnsupportedOperation("noncommuting terms require explicit formula")
    if len(terms)>128:raise q.ResourceLimit("term cap")
    if t==0:return q.Circuit(n)
    return sequence(n,((pauli_rotation(label,2*t*coef),range(n)) for label,coef in terms))

def product_formula(H,time,*,steps,order=1,n=None):
    """Explicit approximation: chronological Lie or symmetric Suzuki order."""
    if not isinstance(H,q.Observable):raise TypeError("expected Observable")
    n=width(H.num_qubits if n is None else n)
    t=_angle(time);steps=_int(steps,1);order=_int(order,1)
    if steps>32 or order not in (1,2):raise q.ResourceLimit("steps <=32; orders 1 or 2")
    terms=_terms(H,n)
    scale=1 if order==1 else .5
    row=[(label,coef*scale) for label,coef in terms]
    if order==2:row+=list(reversed(row))
    # Worst case 4*n+1 gates per term; bound before creating blocks.
    if steps*len(row)*(4*n+1)>4096:raise q.ResourceLimit("formula expansion")
    layer=sequence(n,((pauli_rotation(label,2*t*coef/steps),range(n)) for label,coef in row))
    return power(layer,steps)

def controlled(c,controls=1):
    """Bounded closed-control study, using native synthesis and strict oracle."""
    c=bound(c);k=_int(controls,1);n=c.num_qubits+k
    if n>5 or len(c.to_qiskit().data)>16:
        raise q.ResourceLimit("controlled research width <=5, source <=16 gates")
    native=QuantumCircuit(n)
    native.append(c.to_qiskit().to_gate().control(k),range(n))
    lowered=transpile(native,basis_gates=["h","p","cx","u"],optimization_level=0,
                       seed_transpiler=1101,qubits_initially_zero=False)
    if len(lowered.data)>4096:raise q.ResourceLimit("controlled lowering expansion")
    out=q.from_qiskit(lowered)
    if not np.allclose(Operator(native).data,Operator(out.to_qiskit()).data,atol=1e-9,rtol=0):
        raise q.UnsupportedOperation("strict controlled oracle failed")
    return out

def basis(label):
    if type(label) is not str or not label or set(label)-set("01"):raise ValueError("invalid basis label")
    c=q.Circuit(width(len(label)));active=[i for i,b in enumerate(reversed(label)) if b=="1"]
    return c.x(active) if active else c

def reflection(preparation):
    """2|psi><psi|-I for psi=preparation|0>; strict sign."""
    u=bound(preparation);n=u.num_qubits
    if n==1:zero=q.Circuit(1).z(0)
    else:
        native=q.phase_oracle("0"*n).to_qiskit();native.global_phase+=pi
        zero=q.from_qiskit(native)
    return conjugate(u.inverse(),zero,n=n,compute_wires=range(n),action_wires=range(n))

def parity(n,controls,target):
    n=width(n);cs=wires(controls,n);target=_int(target)
    if target>=n or target in cs:raise ValueError("invalid parity target")
    return q.Circuit(n).cx(pairs=[(c,target) for c in cs])

def graph_state(n,edges):
    n=width(n)
    pairs=tuple(wires(row,n,2) for row in ordered(edges,28,empty=True))
    if len({tuple(sorted(p)) for p in pairs})!=len(pairs):raise ValueError("duplicate undirected edge")
    c=q.Circuit(n).h(range(n))
    return c.cz(pairs=pairs) if pairs else c

def increment(n):
    """Modular increment on n wires, no extra carry register."""
    n=width(n);c=q.Circuit(n)
    for t in reversed(range(1,n)):
        if t==1:c.cx(0,t)
        elif t==2:c.ccx(0,1,t)
        else:c.mcx(range(t),t)
    return c.x(0)

def tensor(a,b):
    a,b=bound(a),bound(b);n=width(a.num_qubits+b.num_qubits)
    return sequence(n,((a,range(a.num_qubits)),(b,range(a.num_qubits,n))))

def syndrome_bit_flip(error=None):
    """Three-data-bit repetition code, two explicit syndrome ancillas."""
    c=q.Circuit.classical(5,2)
    c.cx(0,1).cx(0,2)
    if error is not None:
        error=_int(error)
        if error>2:raise ValueError("invalid data fault")
        c.x(error)
    c.cx(pairs=[(0,3),(1,3),(1,4),(2,4)])
    return c.measure([3,4],[0,1])

def feedforward():
    """Current restricted classical condition, not coherent control."""
    return q.Circuit.classical(2,2).x(0).measure(0,0).if_x(1,0).measure(1,1)
