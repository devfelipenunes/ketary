"""Bounded Python conveniences over the existing native circuit model."""
from collections.abc import Mapping
from itertools import islice
import operator
from ._validation import _int,_limit,ResourceLimit,UnsupportedOperation

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

def _single(c,name,wire,*params):
    # Preserve the common scalar path and existing validation, including bool.
    if type(wire) is int or hasattr(wire,"__index__"):
        return getattr(c.gates,name)(*params,wire)
    selected=_selection(c,wire)
    candidate=c.copy()
    for w in selected:
        getattr(candidate.gates,name)(*params,w)
    c._qc=candidate._qc
    return c

def _pauli_label(n,value):
    if not isinstance(value,Mapping):
        return value
    if len(value)>n:
        raise ValueError("Pauli mapping exceeds width")
    label=["I"]*n
    seen=set()
    for wire,axis in value.items():
        wire=_int(wire)
        if wire>=n or wire in seen or type(axis) is not str or axis not in ("I","X","Y","Z"):
            raise ValueError("invalid local Pauli wire or axis")
        seen.add(wire)
        label[n-1-wire]=axis
    return "".join(label)

class SweepPlan:
    """Frozen bound circuit payloads, zipped rows, never an implicit simulation."""
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
        payloads=tuple(circuit.bind({params[name]:v for name,v in row}).to_json() for row in rows)
        self._rows=rows
        self._payloads=payloads
        self._width=circuit.num_qubits

    @property
    def bindings(self):
        return tuple(dict(row) for row in self._rows)

    def run(self,*,max_bytes=64*1024**2):
        from ._circuit import Circuit
        _limit(self._width,len(self._payloads)+1,budget=max_bytes)
        return tuple(Circuit.from_json(payload).run(max_bytes=max_bytes) for payload in self._payloads)
