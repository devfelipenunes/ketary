"""Bounded Python conveniences over the existing native circuit model."""
from collections.abc import Mapping
from itertools import islice
import operator
from ._validation import _int,_limit,ResourceLimit,UnsupportedOperation,_pauli_label

def _name(name):
    if type(name) is not str or not name.isidentifier() or len(name)>64:
        raise ValueError("expected an identifier of at most 64 characters")
    return name

def _selection(c,wires):
    if isinstance(wires,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected an ordered iterable of wires")
    try:
        selected=tuple(c.gates._wire(w) for w in islice(iter(wires),min(c.num_qubits,4096)+1))
    except TypeError as exc:
        raise ValueError("expected an ordered iterable of wires") from exc
    if not selected or len(selected)>min(c.num_qubits,4096) or len(set(selected))!=len(selected):
        raise ValueError("expected nonempty distinct wires, at most 4096")
    return selected

def _native_batch(c,append):
    """Run a preflighted, phase-neutral native append as a suffix transaction.

    Classical mode retains independent staging. For unitary gate batches
    (including symbolic parameters), native data deletion restores the
    parameter table on ordinary append failures. Not used for composition.
    """
    if c.num_clbits:
        candidate=c._qc.copy()
        append(candidate)
        c._qc=candidate
        return c
    start=len(c._qc.data)
    phase=c._qc.global_phase
    try:
        append(c._qc)
    except Exception:
        del c._qc.data[start:]
        c._qc.global_phase=phase
        raise
    return c


def _single(c,name,wire,*params):
    # Preserve the common scalar path and existing validation, including bool.
    if type(wire) is int or hasattr(wire,"__index__"):
        return getattr(c.gates,name)(*params,wire)
    selected=_selection(c,wire)
    # All supported single-wire methods take real/explicit symbolic angles
    # followed by a wire. Native broadcast preserves supplied wire order.
    values=tuple(c._gate_angle(p) for p in params)
    return _native_batch(c,lambda native:getattr(native,name)(*values,list(selected)))


def _rotation(c,name,theta,wire):
    # Scalars retain the established broadcast path. A sequence of angles
    # requires exactly one value per selected wire; never Cartesian expansion.
    if isinstance(theta,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected a scalar angle or an ordered angle sequence")
    try:
        angles=iter(theta)
    except TypeError:
        return _single(c,name,wire,theta)
    selected=_selection(c,wire)
    values=tuple(islice(angles,len(selected)+1))
    if len(values)!=len(selected):
        raise ValueError("angle and wire sequences must have equal length")
    values=tuple(c._gate_angle(v) for v in values)
    def append(native):
        gate=getattr(native,name)
        for w,v in zip(selected,values,strict=True):
            gate(v,w)
    return _native_batch(c,append)


def _pairs(c,name,a,b,pairs,*params):
    """Explicit ordered pair placement; no implicit zip or Cartesian mode."""
    if pairs is None:
        return getattr(c.gates,name)(*params,a,b)
    if a is not None or b is not None:
        raise ValueError("choose scalar wires or pairs, not both")
    if isinstance(pairs,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected ordered wire pairs")
    gate=c.gates
    selected=[]
    try:
        for row in islice(iter(pairs),10001):
            if isinstance(row,(str,bytes,Mapping,set,frozenset)):
                raise ValueError("expected ordered wire pair")
            pair=tuple(islice(iter(row),3))
            if len(pair)!=2:
                raise ValueError("each pair must contain two distinct wires")
            selected.append(gate._pair(*pair))
    except TypeError as exc:
        raise ValueError("expected ordered wire pairs") from exc
    if not selected:
        raise ValueError("expected at least one wire pair")
    if len(selected)>10000:
        raise ResourceLimit("pair batch supports at most 10000 pairs")
    # Only single-angle gates support aligned rows. Keep the established
    # native scalar broadcast unchanged, including symbolic parameters.
    if len(params)==1:
        theta=params[0]
        if isinstance(theta,(str,bytes,Mapping,set,frozenset)):
            raise ValueError("expected scalar angle or ordered angle sequence")
        try:
            angles=iter(theta)
        except TypeError:
            pass
        else:
            values=tuple(islice(angles,len(selected)+1))
            if len(values)!=len(selected):
                raise ValueError("angle and pair sequences must have equal length")
            values=tuple(c._gate_angle(v) for v in values)
            def append(native):
                method=getattr(native,name)
                for (first,second),angle in zip(selected,values,strict=True):
                    method(angle,first,second)
            return _native_batch(c,append)
    values=tuple(c._gate_angle(p) for p in params)
    first,second=zip(*selected,strict=True)
    return _native_batch(c,lambda native:getattr(native,name)(*values,list(first),list(second)))


class SweepPlan:
    """Private independent native bound circuits; no implicit simulation."""
    def __init__(self,circuit,values):
        from ._circuit import Circuit
        if not isinstance(circuit,Circuit):
            raise TypeError("expected Circuit")
        if circuit.num_clbits:
            raise UnsupportedOperation("sweep requires symbolic unitary circuit")
        if circuit.num_qubits>12 or len(circuit._qc.data)>256:
            raise ResourceLimit("sweep supports <=12 qubits and 256 operations")
        if not isinstance(values,Mapping) or not values or set(values)!={p.name for p in circuit.parameters} or len(values)>32:
            raise ValueError("sweep requires every parameter name")
        columns=[]
        for name,items in values.items():
            if isinstance(items,(str,bytes,Mapping,set,frozenset)):
                raise ValueError("expected ordered numeric sweep values")
            col=tuple(islice(iter(items),33))
            if not 1<=len(col)<=32:
                raise ResourceLimit("sweep requires 1..32 rows")
            columns.append((name,col))
        if len({len(col) for _,col in columns})!=1:
            raise ValueError("sweep columns must have equal length (zipped, not Cartesian)")
        from ._validation import _angle
        rows=tuple(tuple((name,_angle(col[i])) for name,col in columns) for i in range(len(columns[0][1])))
        params={p.name:p for p in circuit.parameters}
        if len(params)!=len(circuit.parameters):
            raise ValueError("sweep requires unique parameter names")
        self._initialize_rows(circuit,rows,params)

    def _initialize_rows(self,circuit,rows,params):
        # Private path only: callers preflight complete, finite, bounded rows.
        # Native assignment returns independent circuits; JSON remains an
        # external replay format, not an in-memory execution transport.
        from ._circuit import Circuit
        # Exact Circuit instances can reuse the complete finite row preflight.
        # Subclasses keep the public bind dispatch. No source snapshot is cached;
        # assignment and validation of evaluated values happen for every row.
        if type(circuit) is Circuit:
            # Iterating caller-owned rows/columns can mutate the source.
            # Recheck completeness once after all user input is consumed,
            # before native assignment; do not rely on a stale parameter view.
            if set(params.values())!=set(circuit._qc.parameters) or {name for name,_ in rows[0]}!=set(params):
                raise ValueError("bindings must cover exactly the template parameters")
            bind=circuit._bind_numeric
        else:
            bind=circuit.bind
        payloads=tuple(bind({params[name]:v for name,v in row}) for row in rows)
        self._rows=rows
        self._payloads=payloads
        self._width=circuit.num_qubits

    @property
    def bindings(self):
        return tuple(dict(row) for row in self._rows)

    def run(self,*,max_bytes=64*1024**2):
        _limit(self._width,len(self._payloads)+1,budget=max_bytes)
        return tuple(payload.run(max_bytes=max_bytes) for payload in self._payloads)


def _sweep_rows(circuit,rows):
    """Transpose explicit parameter rows to the existing bounded sweep plan."""
    from ._validation import _angle
    if circuit.num_clbits:
        raise UnsupportedOperation("sweep requires symbolic unitary circuit")
    params=circuit.parameters
    if circuit.num_qubits>12 or len(circuit._qc.data)>256 or len(params)>32:
        raise ResourceLimit("sweep supports <=12 qubits, 256 operations, 32 parameters")
    if not params:
        raise ValueError("sweep requires at least one parameter")
    if isinstance(rows,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected ordered parameter rows")
    parsed=[]
    try:
        for row in islice(iter(rows),33):
            if isinstance(row,(str,bytes,Mapping,set,frozenset)):
                raise ValueError("expected ordered numeric parameter row")
            values=tuple(islice(iter(row),len(params)+1))
            if len(values)!=len(params):
                raise ValueError("row must cover exactly the native parameter order")
            parsed.append(tuple(_angle(v) for v in values))
    except TypeError as exc:
        raise ValueError("expected ordered parameter rows") from exc
    if not 1<=len(parsed)<=32:
        raise ResourceLimit("sweep requires 1..32 rows")
    names={p.name:p for p in params}
    if len(names)!=len(params):
        raise ValueError("sweep requires unique parameter names")
    # Already validated row-major input. Do not transpose to columns only
    # to validate and transpose it back; retain the same immutable rows.
    plan=SweepPlan.__new__(SweepPlan)
    plan._initialize_rows(circuit,tuple(tuple(zip(names,row,strict=True)) for row in parsed),names)
    return plan


def _evolve(c,observable,time):
    """Exact commuting Pauli evolution; stage a single ordinary circuit."""
    from ._observable import Observable
    from ._circuit import Circuit
    from math import fsum,pi
    symbolic=getattr(c,"_symbolic",False)
    if c.num_clbits or not symbolic:
        c._require_bound()
    if not isinstance(observable,Observable):
        raise TypeError("expected Observable")
    n=c.num_qubits
    if n>8:
        raise ResourceLimit("commuting evolution supports at most eight wires")
    t=c._gate_angle(time)
    unbound=bool(getattr(t,"parameters",()))
    terms=tuple((label,coef) for label,coef in observable.to_dict(n).items() if coef!=0)
    # Deterministic canonical term order; symplectic Pauli parity.
    # Exact evolution is deliberately unavailable for noncommuting sums.
    for i,(left,_) in enumerate(terms):
        for right,_ in terms[i+1:]:
            if sum(a!="I" and b!="I" and a!=b for a,b in zip(left,right,strict=True))%2:
                raise UnsupportedOperation("noncommuting Pauli sum requires explicit approximation")
    if (not unbound and t==0) or not terms:
        return c
    rows=[];phases=[];gate_count=0
    for label,coef in terms:
        angle=c._gate_angle(2*(t*coef))
        active=tuple((i,axis) for i,axis in enumerate(reversed(label)) if axis!="I")
        if not active:
            phases.append(-angle/2)
            continue
        if not getattr(angle,"parameters",()) and angle==0:
            continue
        # Worst case two basis changes per side, two parity ladders and RZ.
        gate_count+=1 if len(active)==1 or (len(active)==2 and active[0][1]==active[1][1]) else 6*len(active)-1
        if gate_count>10000:
            raise ResourceLimit("commuting evolution gate expansion exceeds 10000")
        rows.append((active,angle))
    phase=c._gate_angle(sum(phases) if unbound else fsum(phases))
    # Only one call-local block; no per-term Circuit objects or simulations.
    block=Circuit.symbolic(n) if symbolic else Circuit(n)
    native=block._qc
    native.global_phase=phase
    for active,theta in rows:
        if len(active)==1:
            wire,axis=active[0]
            getattr(native,"r"+axis.lower())(theta,wire)
            continue
        if len(active)==2 and active[0][1]==active[1][1]:
            (a,axis),(b,_)=active
            getattr(native,"r"+axis.lower()*2)(theta,a,b)
            continue
        for wire,axis in active:
            if axis=="X":native.h(wire)
            elif axis=="Y":native.rx(pi/2,wire)
        target=active[-1][0]
        for wire,_ in active[:-1]:native.cx(wire,target)
        native.rz(theta,target)
        for wire,_ in reversed(active[:-1]):native.cx(wire,target)
        for wire,axis in reversed(active):
            if axis=="X":native.h(wire)
            elif axis=="Y":native.rx(-pi/2,wire)
    # Existing application transaction preserves phase/checkpoint semantics.
    return c.apply(block)
