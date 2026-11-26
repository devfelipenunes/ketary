"""Immutable real Pauli sums, delegated to existing snapshot mathematics.

No new simulator, implicit execution or non-Hermitian operator algebra.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import islice
from numbers import Real
from math import fsum
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

    @classmethod
    def from_qiskit(cls,operator):
        """Import a bounded real Hermitian native Pauli sum, without execution."""
        from qiskit.quantum_info import SparsePauliOp
        if not isinstance(operator,SparsePauliOp):
            raise TypeError("expected SparsePauliOp")
        if not 1<=operator.num_qubits<=_MAX_WIDTH or operator.size>4096:
            raise ResourceLimit("native observable exceeds width or input-term limit")
        # Native conversion includes Pauli phases. Aggregate duplicates before
        # checking Hermiticity; use no numerical truncation or imaginary tolerance.
        terms={}
        for label,value in operator.to_list():
            if type(label) is not str or set(label)-set("IXYZ"):
                raise ValueError("expected canonical native Pauli labels")
            try:
                coefficient=complex(value)
            except (ValueError,TypeError,OverflowError) as exc:
                raise ValueError("native coefficients must be finite numeric values") from exc
            real,imag=_real(coefficient.real),_real(coefficient.imag)
            terms.setdefault(label,[]).append(complex(real,imag))
        terms={label:_sum_complex(values) for label,values in terms.items()}
        if any(value.imag!=0 for value in terms.values()):
            raise ValueError("native observable must have real aggregate coefficients")
        cleaned={label:value.real for label,value in terms.items() if value.real}
        if len(cleaned)>_MAX_TERMS:
            raise ResourceLimit("observable term limit exceeded")
        return cls(cleaned or {"I"*operator.num_qubits:0.0})

    @property
    def num_qubits(self):
        """Minimum embedding width, including explicitly declared identities."""
        return self._width

    def to_dict(self,num_qubits=None):
        n=self._width if num_qubits is None else _int(num_qubits,1)
        if n<self._width or n>_MAX_WIDTH:
            raise ValueError("observable embedding must preserve width and fit 62 qubits")
        return {label.rjust(n,"I"):value for label,value in self._terms}

    def on(self,wires,*,width):
        """Return this local observable embedded in ordered absolute wires.

        Local bit i maps to wires[i]. Identity and zero retain explicit
        width; no execution, mutation or implicit ancillary qubits.
        """
        n=_int(width,1)
        if n>_MAX_WIDTH:
            raise ResourceLimit("embedding width exceeds 62")
        if isinstance(wires,(str,bytes,Mapping,set,frozenset)):
            raise ValueError("ordered wires required")
        k=self._width
        try:
            ws=tuple(_int(w) for w in islice(iter(wires),k+1))
        except TypeError as exc:
            raise ValueError("ordered wires required") from exc
        if len(ws)!=k or len(set(ws))!=k or any(w>=n for w in ws):
            raise ValueError("exact distinct local-to-global wire mapping required")
        out={}
        for label,coef in self._terms:
            axes=["I"]*n
            for i,w in enumerate(ws):
                axes[n-1-w]=label[k-1-i]
            out["".join(axes)]=coef
        return Observable(out)

    def to_qiskit(self,num_qubits=None):
        from qiskit.quantum_info import SparsePauliOp
        return SparsePauliOp.from_list(list(self.to_dict(num_qubits).items()))

    def product(self,other):
        """Ordered AB as a native complex Pauli sum."""
        from qiskit.quantum_info import SparsePauliOp
        return SparsePauliOp.from_list(list(_pauli_product(self,other).items()))

    def commutator(self,other):
        """AB-BA as a native complex Pauli sum."""
        from qiskit.quantum_info import SparsePauliOp
        return SparsePauliOp.from_list(list(_pauli_product(self,other,mode="commutator").items()))

    def anticommutator(self,other):
        """AB+BA of Hermitian inputs is Hermitian."""
        return Observable({p:_real(v.real) for p,v in _pauli_product(self,other,mode="anticommutator").items()})

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


def _sum_complex(values):
    """Compensated aggregation of finite rounded contributions, no truncation."""
    try:
        real=fsum(z.real for z in values)
        imag=fsum(z.imag for z in values)
    except (OverflowError,ValueError) as exc:
        raise ValueError("Pauli coefficient sum exceeds finite range") from exc
    return complex(_real(real),_real(imag))


def _pauli_product(left,right,*,mode="product"):
    if not isinstance(right,Observable):
        raise TypeError("expected Observable")
    n=max(left.num_qubits,right.num_qubits)
    a,b=left.to_dict(n),right.to_dict(n)
    if len(a)*len(b)>4096:
        raise ResourceLimit("Pauli product exceeds 4096 term pairs")
    table={("X","Y"):("Z",1j),("Y","Z"):("X",1j),("Z","X"):("Y",1j),
           ("Y","X"):("Z",-1j),("Z","Y"):("X",-1j),("X","Z"):("Y",-1j)}
    out={}
    for p,x in a.items():
        for q,y in b.items():
            phase=1+0j
            label=[]
            for u,v in zip(p,q,strict=True):
                if u=="I":label.append(v)
                elif v=="I":label.append(u)
                elif u==v:label.append("I")
                else:
                    axis,factor=table[u,v]
                    label.append(axis)
                    phase*=factor
            if mode=="commutator":
                phase=2j*phase.imag
            elif mode=="anticommutator":
                phase=2*phase.real
            if not phase:
                continue
            key="".join(label)
            value=phase*x*y
            out.setdefault(key,[]).append(complex(_real(value.real),_real(value.imag)))
    out={label:_sum_complex(values) for label,values in out.items()}
    out={p:v for p,v in out.items() if v} or {"I"*n:0j}
    if len(out)>256:
        raise ResourceLimit("Pauli product exceeds 256 output terms")
    return dict(sorted(out.items()))
