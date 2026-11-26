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

    Symbolic and classical modes retain independent staging: a failed native
    parameter insertion must not leak a parameter-table or classical change.
    The bound path only uses standard native gate methods.
    """
    if c.num_clbits or getattr(c,"_symbolic",False):
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
        # Native assignment returns independent circuits; JSON remains an
        # external replay format, not an in-memory execution transport.
        payloads=tuple(circuit.bind({params[name]:v for name,v in row}) for row in rows)
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
    return SweepPlan(circuit,{p.name:tuple(row[i] for row in parsed)
                              for i,p in enumerate(params)})
