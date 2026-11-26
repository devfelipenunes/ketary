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


def _shifted_bound_circuit(bound,offsets):
    """Own and validate one disposable native shift, never execute it.

    Offsets are already bounded by the derivative planner, in radians.
    Keep native gate copies and full validation before any simulation.
    """
    from ._validation import _real
    from ._circuit import Circuit
    raw=bound.copy()
    for index,shift in offsets:
        item=raw.data[index]
        gate=item.operation.to_mutable()
        gate.params=[_real(float(gate.params[0])+shift)]
        raw.data[index]=item.replace(operation=gate)
    return Circuit._from_native(raw,owned=True)


def _expectation_jacobian(c,bindings,observables,*,max_bytes):
    """Bounded occurrence-wise two/four-point shifts; not a state derivative."""
    from math import pi,fsum
    from ._validation import _real
    from ._observable import Observable
    if c.num_clbits:
        raise UnsupportedOperation("unitary expectation derivative only")
    if c.num_qubits>8 or len(c.parameters)>32 or len(c._qc.data)>256:
        raise ResourceLimit("Jacobian supports <=8 wires, 32 parameters, 256 gates")
    _limit(c.num_qubits,3,budget=max_bytes)
    # Own the template before consuming user iterables/mappings.
    template=c.copy()
    params=template.parameters
    if not isinstance(bindings,Mapping) or set(bindings)!=set(params):
        raise ValueError("complete native parameter identity mapping required")
    vals={p:_real(bindings[p]) for p in params}
    if isinstance(observables,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected ordered observables")
    try:
        obs=tuple(islice(iter(observables),9))
    except TypeError as exc:
        raise ValueError("expected ordered observables") from exc
    if not 1<=len(obs)<=8:
        raise ResourceLimit("Jacobian requires 1..8 observables")
    if any(not isinstance(H,Observable) or H.num_qubits>template.num_qubits for H in obs):
        raise ValueError("expected compatible real Observable objects")
    def numeric(expr):
        try:
            if getattr(expr,"parameters",()):
                expr=expr.bind({p:vals[p] for p in expr.parameters})
            value=complex(expr)
        except (TypeError,ValueError,OverflowError,ZeroDivisionError) as exc:
            raise ValueError("nonfinite or unbound derivative expression") from exc
        if value.imag!=0:
            raise ValueError("derivative expression must be real")
        return _real(value.real)
    supported={"rx","ry","rz","rxx","ryy","rzz","p","cp"}
    controlled={"crx","cry","crz"}
    staged=[]
    shift_count=0
    for i,item in enumerate(template._qc.data):
        for j,angle in enumerate(item.params):
            present=getattr(angle,"parameters",())
            if not present:
                continue
            if item.operation.name not in supported|controlled or j!=0:
                raise UnsupportedOperation("generator not qualified for expectation shift")
            weights=tuple(numeric(angle.gradient(p)) if p in present else 0. for p in params)
            if any(weights):
                four=item.operation.name in controlled
                shift_count+=4 if four else 2
                if shift_count>128:
                    raise ResourceLimit("Jacobian supports at most 128 shifted circuits")
                staged.append((i,weights,four))
    # Bind even for zero derivatives, including symbolic global phase.
    bound=template.bind(vals)._qc
    pairs=[]
    # Complete shifted circuit validation before starting any simulation.
    for index,weights,four in staged:
        shifted_pair=[]
        shifts=(pi/2,-pi/2,pi,-pi) if four else (pi/2,-pi/2)
        for shift in shifts:
            shifted_pair.append(_shifted_bound_circuit(bound,((index,shift),)))
        pairs.append((weights,*shifted_pair))
    contributions=[[[] for _ in params] for _ in obs]
    from math import sqrt
    correction=(1-sqrt(2))/4
    for weights,plus,minus,*extra in pairs:
        left=plus.run(max_bytes=max_bytes).math.expectations(obs)
        right=minus.run(max_bytes=max_bytes).math.expectations(obs)
        if extra:
            far_left,far_right=(r.run(max_bytes=max_bytes).math.expectations(obs) for r in extra)
        else:
            far_left=far_right=(0.,)*len(obs)
        for row,(a,b,u,v) in zip(contributions,zip(left,right,far_left,far_right,strict=True),strict=True):
            diff=.5*(a-b)
            if extra:
                diff=fsum((diff,correction*(u-v)))
            for terms,weight in zip(row,weights,strict=True):
                terms.append(_real(diff*weight))
    return tuple(tuple(_real(fsum(terms)) for terms in row) for row in contributions)


def _evolve_product(c,observable,*,time,steps,order):
    """Stage an explicitly approximate ordered Pauli product formula."""
    from ._observable import Observable
    from ._circuit import Circuit
    c._require_bound()
    if not isinstance(observable,Observable):
        raise TypeError("expected Observable")
    n=c.num_qubits
    if n>8:
        raise ResourceLimit("product evolution supports <=8 wires")
    t=c._gate_angle(time)
    steps,order=_int(steps,1),_int(order,1)
    if steps>64:
        raise ResourceLimit("product evolution supports <=64 steps")
    if order not in (1,2):
        raise ValueError("product formula order must be one or two")
    terms=tuple((p,v) for p,v in observable.to_dict(n).items() if v)
    count=sum(max(1,6*sum(a!="I" for a in p)-1) for p,_ in terms)
    if count*steps*order>10000:
        raise ResourceLimit("product formula exceeds 10000 estimated instructions")
    if not terms or t==0:
        return c
    block=Circuit(n)
    sequence=terms if order==1 else terms+terms[::-1]
    dt=t/(steps*order)
    for p,v in sequence:
        block.evolve(Observable({p:v}),time=dt)
    return c.apply(block,times=steps)


def _quantum_geometric_tensor(c,bindings,*,max_bytes):
    """Projected state derivatives for qualified one-angle generators."""
    from math import pi,sqrt
    import numpy as np
    from ._validation import _real
    if c.num_clbits:
        raise UnsupportedOperation("QGT requires ideal unitary evolution")
    if c.num_qubits>8 or len(c.parameters)>16 or len(c._qc.data)>256:
        raise ResourceLimit("QGT supports <=8 wires, 16 parameters, 256 gates")
    template=c.copy()
    params=template.parameters
    _limit(template.num_qubits,2*len(params)+8,budget=max_bytes)
    if not isinstance(bindings,Mapping) or set(bindings)!=set(params):
        raise ValueError("complete native parameter identity mapping required")
    values={p:_real(bindings[p]) for p in params}
    def numeric(expr):
        try:
            if getattr(expr,"parameters",()):
                expr=expr.bind({p:values[p] for p in expr.parameters})
            z=complex(expr)
        except (TypeError,ValueError,OverflowError,ZeroDivisionError) as exc:
            raise ValueError("invalid state derivative expression") from exc
        if z.imag!=0:
            raise ValueError("state derivative expression must be real")
        return _real(z.real)
    rotations={"rx","ry","rz","rxx","ryy","rzz","crx","cry","crz"}
    phases={"p","cp"}
    staged=[]
    for i,item in enumerate(template._qc.data):
        for j,angle in enumerate(item.params):
            present=getattr(angle,"parameters",())
            if not present:
                continue
            name=item.operation.name
            if j!=0 or name not in rotations|phases:
                raise UnsupportedOperation("generator not qualified for QGT state shift")
            weights=tuple(numeric(angle.gradient(p)) if p in present else 0. for p in params)
            if any(weights):
                factor=.5 if name in phases else 1/(2*sqrt(2))
                staged.append((i,weights,factor))
                if len(staged)>32:
                    raise ResourceLimit("QGT supports <=32 active occurrences")
    bound=template.bind(values)
    if not params:
        return ()
    # Validate all shift circuits before any simulation, including global phase binding.
    pairs=[]
    for index,weights,factor in staged:
        pair=[]
        for sign in (1,-1):
            pair.append(_shifted_bound_circuit(bound._qc,((index,sign*pi/2),)))
        pairs.append((weights,factor,*pair))
    psi=bound.run(max_bytes=max_bytes).math.statevector()
    derivatives=np.zeros((psi.size,len(params)),dtype=complex)
    with np.errstate(over="ignore",invalid="ignore"):
        for weights,factor,plus,minus in pairs:
            delta=factor*(plus.run(max_bytes=max_bytes).math.statevector()-minus.run(max_bytes=max_bytes).math.statevector())
            for j,w in enumerate(weights):
                if w:
                    derivatives[:,j]+=w*delta
        # The omitted derivative of native global phase lies along psi and vanishes.
        # No dense 2**n by 2**n projector is allocated.
        projected=derivatives-psi[:,None]*(psi.conj()@derivatives)[None,:]/np.vdot(psi,psi).real
        Q=projected.conj().T@projected
    if not np.isfinite(Q).all():
        raise ArithmeticError("QGT is not finite")
    return tuple(tuple(complex(z) for z in row) for row in Q)


def _expectation_hessian(c,bindings,observables,*,max_bytes):
    """Bounded second-order chain rule with exact ideal occurrence shifts."""
    from math import pi,sqrt,fsum
    from ._validation import _real
    from ._observable import Observable
    if c.num_clbits:
        raise UnsupportedOperation("Hessian requires ideal unitary evolution")
    if c.num_qubits>8 or len(c.parameters)>8 or len(c._qc.data)>256:
        raise ResourceLimit("Hessian supports <=8 wires, 8 parameters, 256 gates")
    _limit(c.num_qubits,3,budget=max_bytes)
    template=c.copy()
    params=template.parameters
    if not isinstance(bindings,Mapping) or set(bindings)!=set(params):
        raise ValueError("complete native parameter identity mapping required")
    values={p:_real(bindings[p]) for p in params}
    if isinstance(observables,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected ordered observables")
    try:
        obs=tuple(islice(iter(observables),9))
    except TypeError as exc:
        raise ValueError("expected ordered observables") from exc
    if not 1<=len(obs)<=8:
        raise ResourceLimit("Hessian requires 1..8 observables")
    if any(not isinstance(H,Observable) or H.num_qubits>template.num_qubits for H in obs):
        raise ValueError("expected compatible real Observable objects")
    def numeric(expr):
        try:
            if getattr(expr,"parameters",()):
                expr=expr.bind({p:values[p] for p in expr.parameters})
            z=complex(expr)
        except (TypeError,ValueError,OverflowError,ZeroDivisionError) as exc:
            raise ValueError("invalid second derivative expression") from exc
        if z.imag!=0:
            raise ValueError("second derivative expression must be real")
        return _real(z.real)
    two=((1,.5),(-1,-.5))
    controlled_coefficient=(1-sqrt(2))/4
    four=two+((2,controlled_coefficient),(-2,-controlled_coefficient))
    regular={"rx","ry","rz","rxx","ryy","rzz","p","cp"}
    controlled={"crx","cry","crz"}
    active=[]
    for index,item in enumerate(template._qc.data):
        for j,angle in enumerate(item.params):
            present=getattr(angle,"parameters",())
            if not present:
                continue
            name=item.operation.name
            if j!=0 or name not in regular|controlled:
                raise UnsupportedOperation("generator not qualified for Hessian")
            gradients=tuple(angle.gradient(p) if p in present else 0. for p in params)
            weights=tuple(numeric(g) for g in gradients)
            second=tuple(tuple(numeric(g.gradient(p)) if p in getattr(g,"parameters",()) else 0. for p in params) for g in gradients)
            if any(weights) or any(any(row) for row in second):
                active.append((index,weights,second,four if name in controlled else two))
                if len(active)>8:
                    raise ResourceLimit("Hessian supports <=8 active occurrences")
    bound=template.bind(values)._qc
    # Canonical sparse shift keys in integer units of pi/2. These describe
    # disposable experiments, not a second circuit model.
    def key(i,shift,j=None,other=0):
        offsets={i:shift}
        if j is not None:
            offsets[j]=offsets.get(j,0)+other
        return tuple(sorted((k,v) for k,v in offsets.items() if v))
    first={}
    pairs={}
    needed=set()
    for i,weights,second,rule in active:
        if any(any(row) for row in second):
            first[i]=tuple((key(i,s),a) for s,a in rule)
            needed.update(k for k,_ in first[i])
    for pos,(i,wi,_,ri) in enumerate(active):
        if not any(wi):
            continue
        for j,wj,_,rj in active[pos:]:
            if not any(wj):
                continue
            terms={}
            for s,a in ri:
                for t,b in rj:
                    k=key(i,s,j,t)
                    terms.setdefault(k,[]).append(a*b)
            pairs[i,j]=tuple((k,fsum(v)) for k,v in terms.items() if fsum(v))
            needed.update(k for k,_ in pairs[i,j])
    if len(needed)>256:
        raise ResourceLimit("Hessian supports <=256 distinct shifted circuits")
    # All native copies and numeric angles validated before any execution.
    circuits={}
    for k in sorted(needed):
        circuits[k]=_shifted_bound_circuit(bound,((index,offset*pi/2) for index,offset in k))
    evaluated={k:run.run(max_bytes=max_bytes).math.expectations(obs) for k,run in circuits.items()}
    def shifted(terms,o):
        return _real(fsum(_real(a*evaluated[k][o]) for k,a in terms))
    output=[]
    for o in range(len(obs)):
        D={i:shifted(v,o) for i,v in first.items()}
        DD={ij:shifted(v,o) for ij,v in pairs.items()}
        rows=[[0. for _ in params] for _ in params]
        for p in range(len(params)):
            for q in range(p,len(params)):
                contributions=[]
                for pos,(i,wi,second,_) in enumerate(active):
                    if i in D:
                        contributions.append(_real(D[i]*second[p][q]))
                    for j,wj,_,_ in active[pos:]:
                        if (i,j) not in DD:
                            continue
                        weight=wi[p]*wj[q] if i==j else fsum((wi[p]*wj[q],wj[p]*wi[q]))
                        contributions.append(_real(DD[i,j]*_real(weight)))
                rows[p][q]=rows[q][p]=_real(fsum(contributions))
        output.append(tuple(tuple(row) for row in rows))
    return tuple(output)
