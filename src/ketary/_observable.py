"""Immutable real Pauli sums, delegated to existing snapshot mathematics.

No new simulator, implicit execution or non-Hermitian operator algebra.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Real
from ._validation import _int,_real,ResourceLimit

_MAX_WIDTH=62
_MAX_TERMS=256

@dataclass(frozen=True,init=False)
class Observable:
    """Real coefficients over full-width Pauli labels in native bit order."""
    _terms: tuple[tuple[str,float],...]
    _width: int

    def __init__(self,terms):
        if not isinstance(terms,Mapping) or not 1<=len(terms)<=_MAX_TERMS:
            raise ValueError("expected 1..256 Pauli terms")
        width=None
        cleaned={}
        for label,value in terms.items():
            if type(label) is not str or not 1<=len(label)<=_MAX_WIDTH or set(label)-set("IXYZ"):
                raise ValueError("expected 1..62 uppercase Pauli symbols")
            if width is None:
                width=len(label)
            if len(label)!=width:
                raise ValueError("Pauli labels must have identical width")
            coefficient=_real(value)
            if coefficient:
                cleaned[label]=coefficient
        object.__setattr__(self,"_width",width)
        object.__setattr__(self,"_terms",tuple(sorted(cleaned.items())) or (("I"*width,0.0),))

    @property
    def num_qubits(self):
        """Minimum embedding width, including explicitly declared identities."""
        return self._width

    def to_dict(self,num_qubits=None):
        n=self._width if num_qubits is None else _int(num_qubits,1)
        if n<self._width or n>_MAX_WIDTH:
            raise ValueError("observable embedding must preserve width and fit 62 qubits")
        return {label.rjust(n,"I"):value for label,value in self._terms}

    def to_qiskit(self,num_qubits=None):
        from qiskit.quantum_info import SparsePauliOp
        return SparsePauliOp.from_list(list(self.to_dict(num_qubits).items()))

    def __add__(self,other):
        if isinstance(other,Real):
            other=Observable({"I":_real(other)})
        if not isinstance(other,Observable):
            return NotImplemented
        n=max(self.num_qubits,other.num_qubits)
        result=self.to_dict(n)
        for label,value in other.to_dict(n).items():
            result[label]=_real(result.get(label,0.0)+value)
        result={label:value for label,value in result.items() if value} or {"I"*n:0.0}
        if len(result)>_MAX_TERMS:
            raise ResourceLimit("observable term limit exceeded")
        return Observable(result)

    def __radd__(self,other):
        return self+other

    def __neg__(self):
        return self*(-1)

    def __sub__(self,other):
        if isinstance(other,Observable):
            return self+(-other)
        if isinstance(other,Real):
            return self+(-_real(other))
        return NotImplemented

    def __rsub__(self,other):
        if isinstance(other,(Observable,Real)):
            return (-self)+other
        return NotImplemented

    def __mul__(self,other):
        if not isinstance(other,Real):
            return NotImplemented
        factor=_real(other)
        return Observable({label:_real(value*factor) for label,value in self._terms})

    def __rmul__(self,other):
        return self*other

    def __matmul__(self,other):
        """Disjoint-support tensor product only, on absolute wire indices."""
        if not isinstance(other,Observable):
            return NotImplemented
        n=max(self.num_qubits,other.num_qubits)
        left,right=self.to_dict(n),other.to_dict(n)
        if len(left)*len(right)>4096:
            raise ResourceLimit("observable product work limit exceeded")
        support=lambda terms:{i for label,value in terms.items() if value for i,axis in enumerate(label) if axis!="I"}
        if support(left)&support(right):
            raise ValueError("tensor product requires disjoint nonidentity wire support")
        result={}
        for a,x in left.items():
            for b,y in right.items():
                label="".join(i if i!="I" else j for i,j in zip(a,b,strict=True))
                result[label]=_real(result.get(label,0.0)+x*y)
        result={label:value for label,value in result.items() if value} or {"I"*n:0.0}
        if len(result)>_MAX_TERMS:
            raise ResourceLimit("observable term limit exceeded")
        return Observable(result)

def _local(axis,wire):
    wire=_int(wire)
    if wire>=_MAX_WIDTH:
        raise ResourceLimit("observable wire index exceeds 61")
    return Observable({axis+"I"*wire:1.0})

def X(wire):
    return _local("X",wire)

def Y(wire):
    return _local("Y",wire)

def Z(wire):
    return _local("Z",wire)

def I(wire=0):
    return _local("I",wire)
