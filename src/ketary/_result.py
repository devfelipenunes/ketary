"""Independent result snapshots and mathematical checks."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import numpy as np
from ._validation import _int, _tol, _real, _limit, ResourceLimit

@dataclass(frozen=True)
class CheckResult:
    status: str
    actual: float | None
    expected: float | None
    tolerance: float
    detail: str = ""

    def to_dict(self):
        return asdict(self)

    def render(self):
        return f"{self.status}: actual={self.actual}, expected={self.expected}, tolerance={self.tolerance}; {self.detail}"

    def to_json(self):
        import json
        return json.dumps(self.to_dict(),sort_keys=True,allow_nan=False)

    def require(self):
        if self.status != "PASS":
            raise AssertionError(self.render())
        return self

    def __bool__(self):
        raise TypeError("use .status or .require()")

def _residual(actual,expected,ignore_global_phase,atol):
    t=_tol(atol)
    if type(ignore_global_phase) is not bool:
        raise ValueError("ignore_global_phase must be bool")
    if actual.shape!=expected.shape:
        raise ValueError("dimension mismatch")
    if ignore_global_phase:
        overlap=np.vdot(expected,actual)
        if abs(overlap)>0:
            actual=actual*(np.conj(overlap)/abs(overlap))
    error=float(np.max(np.abs(actual-expected)))
    return CheckResult("PASS" if error<=t else "FAIL",error,0,t,
                       "max absolute residual; phase "+("ignored" if ignore_global_phase else "preserved"))

def _topk_exact_chunks(data,k):
    """Bounded ranking with exactly the original scalar probability scores."""
    selected=np.empty(0,dtype=np.int64)
    scores=np.empty(0,dtype=np.float64)
    for start in range(0,len(data),1024):
        block=data[start:start+1024]
        indices=np.arange(start,start+len(block),dtype=np.int64)
        # Do not vectorize complex magnitude: rounding near ties can change
        # rank relative to the public scalar heap contract.
        probabilities=np.fromiter((abs(value)**2 for value in block),
                                  dtype=np.float64,count=len(block))
        order=np.lexsort((indices,-probabilities))[:k]
        selected=np.concatenate((selected,indices[order]))
        scores=np.concatenate((scores,probabilities[order]))
        keep=np.lexsort((selected,-scores))[:k]
        selected,scores=selected[keep],scores[keep]
    return tuple(int(i) for i in selected)


def _accumulate_pauli_chunks(state,out,terms,chunk):
    """Accumulate real weighted Pauli action without dense operators.

    Input j maps to j XOR xmask; Y contributes i and Z/Y parity
    contributes (-1)**popcount(j & zmask). Each permutation is unique.
    Scratch stays local to this function, released before variance reduction.
    """
    for label,coefficient in terms:
        if not coefficient:
            continue
        x=z=y=0
        for i,axis in enumerate(reversed(label)):
            if axis in "XY":x|=1<<i
            if axis in "YZ":z|=1<<i
            if axis=="Y":y+=1
        phase=1j**y
        for start in range(0,state.size,chunk):
            j=np.arange(start,min(start+chunk,state.size),dtype=np.int64)
            parity=j&z
            parity^=parity>>32
            parity^=parity>>16
            parity^=parity>>8
            parity^=parity>>4
            parity^=parity>>2
            parity^=parity>>1
            out[j^x]+=coefficient*phase*(1-2*(parity&1))*state[j]


class Result:
    """Independent ideal pure-state snapshot; no circuit reference or re-execution."""

    def __init__(self, amplitudes):
        a = np.asarray(amplitudes, dtype=np.complex128)
        self._initialize(a, take_ownership=False)

    @classmethod
    def _from_evolution(cls, amplitudes, *, borrowed=None):
        """Consume a private, fresh native evolution output, never public input."""
        a=np.asarray(amplitudes,dtype=np.complex128)
        owned=(type(a) is np.ndarray and a.flags.owndata and a.flags.c_contiguous
               and a.flags.writeable and (borrowed is None or not np.shares_memory(a,borrowed)))
        result=cls.__new__(cls)
        result._initialize(a,take_ownership=owned)
        return result

    def _initialize(self,a,*,take_ownership):
        if a.ndim != 1 or a.size < 2 or a.size & (a.size-1):
            raise ValueError("state must have dimension 2**n, n>=1")
        norm_sq=float(np.vdot(a,a).real)
        if not np.isfinite(a).all() or not math.isclose(norm_sq,1,rel_tol=0,abs_tol=1e-9):
            raise ValueError("state must be finite and normalized")
        self._norm_sq = norm_sq
        self._data = a if take_ownership else a.copy()
        self._data.flags.writeable = False
        self._n = a.size.bit_length()-1

    @property
    def num_qubits(self):
        return self._n

    @property
    def math(self):
        return _Math(self)

    @property
    def test(self):
        return _Checks(self)

    @property
    def visualize(self):
        from ._visualization import _ResultVisualize
        return _ResultVisualize(self)

    def evidence(self, *, bits=(), paulis=()):
        """Explicit evidence from this snapshot."""
        from ._inspection import result_evidence
        return result_evidence(self,bits=bits,paulis=paulis)

    def verify(self, *, probabilities=None, expectations=None, normalized=False, atol=1e-9):
        """Aggregate named checks, never execute a circuit."""
        from ._inspection import verify_result
        from ._reports import SnapshotReport
        return SnapshotReport(verify_result(self,probabilities=probabilities,expectations=expectations,normalized=normalized,atol=atol))

    def sample(self, *, shots, seed=None, max_outcomes=65536, wires=None):
        shots = _int(shots,1)
        if shots>np.iinfo(np.int64).max:
            raise ResourceLimit("shots exceed signed 64-bit range")
        if wires is not None:
            # Explicit final Z-basis sampling of selected wires, without collapse.
            cap=_int(max_outcomes,1)
            if seed is not None:
                seed=_int(seed)
            probabilities=self.math.marginal_probabilities(wires,max_outcomes=cap)
            p=np.array(list(probabilities.values()))
            p/=p.sum()
            counts=np.random.default_rng(seed).multinomial(shots,p)
            return {key:int(v) for key,v in zip(probabilities,counts,strict=True) if v}
        if min(shots,self._data.size)>_int(max_outcomes,1):
            raise ResourceLimit("potential sample dictionary exceeds outcome limit")
        if seed is not None:
            seed = _int(seed)
        p = np.abs(self._data)
        np.square(p,out=p)
        p /= p.sum()
        counts = np.random.default_rng(seed).multinomial(shots, p)
        # Same seeded native multinomial; enumerate only populated bins in
        # ascending order. Output index allocation is bounded by max_outcomes.
        return {format(i,f"0{self._n}b"):int(counts[i]) for i in np.flatnonzero(counts)}

class _Math:
    def __init__(self, result):
        self._r = result

    def statevector(self, *, max_bytes=64*1024**2):
        _limit(self._r._n,budget=max_bytes)
        return self._r._data.copy()

    def amplitude(self,bits):
        """Amplitude of a computational basis ket, in q[n-1]...q[0] order."""
        if not isinstance(bits,str) or len(bits)!=self._r._n or any(b not in "01" for b in bits):
            raise ValueError("invalid bit string")
        return complex(self._r._data[int(bits,2)])

    def probability(self,bits):
        return float(abs(self.amplitude(bits))**2/self._r._norm_sq)

    def explain_probability(self,bits):
        """Deterministic, numerical Born-rule explanation, not symbolic proof."""
        a=self.amplitude(bits)
        p=self.probability(bits)
        return f"p(|{bits}>) = |{a.real:.12g}{a.imag:+.12g}j|^2 / {self._r._norm_sq:.12g} = {p:.12g}"

    def table(self, bits=None, *, max_rows=16):
        """Bounded basis table; default rows are the first basis indices.

        Explicit labels preserve caller order. The default is a prefix,
        not a ranking by probability. No state copy or re-execution.
        """
        cap=_int(max_rows,1)
        if bits is None:
            labels=[format(i,f"0{self._r._n}b") for i in range(min(cap,self._r._data.size))]
            omitted=self._r._data.size-len(labels)
        else:
            from itertools import islice
            if isinstance(bits,str):
                raise ValueError("pass an iterable of basis labels, not one string")
            labels=list(islice(iter(bits),cap+1))
            if len(labels)>cap:
                raise ResourceLimit("basis table exceeds row limit")
            omitted=0
            if any(not isinstance(label,str) or len(label)!=self._r._n or any(b not in "01" for b in label) for label in labels):
                raise ValueError("invalid bit string")
        rows=["basis | amplitude | probability"]
        for label in labels:
            a=self.amplitude(label)
            rows.append(f"{label} | {a.real:.8g}{a.imag:+.8g}j | {self.probability(label):.8g}")
        if omitted:
            rows.append(f"... {omitted} basis rows omitted")
        return "\n".join(rows)

    def expectation(self,pauli):
        """Expectation of a Hermitian Pauli string, leftmost character is q[n-1]."""
        from ._observable import Observable
        if isinstance(pauli,Observable):
            return self.observable(pauli.to_dict(self._r._n))
        from ._validation import _pauli_label
        pauli=_pauli_label(self._r._n,pauli)
        if not isinstance(pauli,str) or len(pauli)!=self._r._n or any(p not in "IXYZ" for p in pauli):
            raise ValueError("expected a full-width uppercase I/X/Y/Z Pauli label")
        from qiskit.quantum_info import Statevector
        return self._native_pauli_value(Statevector(self._r._data),pauli)

    def _native_pauli_value(self,state,label):
        """One validated Pauli query; common numerical acceptance policy."""
        from qiskit.quantum_info import Pauli
        value=complex(state.expectation_value(Pauli(label)))
        if not math.isfinite(value.real) or not math.isfinite(value.imag) or abs(value.imag)>1e-9:
            raise ArithmeticError("invalid Hermitian Pauli expectation")
        normalized=value.real/self._r._norm_sq
        # Scalar only: preserve clipping and signed zero without a NumPy ufunc.
        if normalized>1:
            return 1.0
        if normalized< -1:
            return -1.0
        return float(normalized)

    def _native_pauli_values(self,labels):
        """Call-local native handle, only after complete caller preflight."""
        from qiskit.quantum_info import Statevector
        state=Statevector(self._r._data)
        return {label:self._native_pauli_value(state,label) for label in labels}

    def expectation_complex(self,operator,*,max_work=64*1024**2):
        """Explicit native complex Pauli expectation; no Hermitian coercion."""
        from qiskit.quantum_info import SparsePauliOp
        if not isinstance(operator,SparsePauliOp):
            raise TypeError("expected native SparsePauliOp")
        if operator.num_qubits!=self._r._n:
            raise ValueError("expected full-width Pauli operator")
        if not 1<=operator.size<=256:
            raise ResourceLimit("complex expectation supports 1..256 Pauli terms")
        work=_int(max_work,1)
        if operator.size*self._r._data.size>work:
            raise ResourceLimit("complex expectation work exceeds Pauli-state budget")
        terms=[]
        for label,coefficient in operator.to_list():
            if type(label) is not str or len(label)!=self._r._n or set(label)-set("IXYZ"):
                raise ValueError("expected canonical native Pauli labels")
            try:
                value=complex(coefficient)
            except (TypeError,ValueError,OverflowError) as exc:
                raise ValueError("expected finite complex coefficient") from exc
            terms.append((label,_real(value.real),_real(value.imag)))
        cache=self._native_pauli_values(sorted({row[0] for row in terms}))
        try:
            real=math.fsum(re*cache[label] for label,re,im in terms)
            imag=math.fsum(im*cache[label] for label,re,im in terms)
        except (OverflowError,ValueError) as exc:
            raise ArithmeticError("complex expectation is not finite") from exc
        if not math.isfinite(real) or not math.isfinite(imag):
            raise ArithmeticError("complex expectation is not finite")
        return complex(real,imag)

    def expectations(self,observables,*,max_work=64*1024**2):
        """Ordered real expectations; validate first, reuse unique Pauli terms."""
        from collections.abc import Mapping
        from itertools import islice
        from ._observable import Observable
        from ._validation import _pauli_label
        work=_int(max_work,1)
        if isinstance(observables,(str,bytes,Mapping,set,frozenset)):
            raise ValueError("expected an ordered iterable of observables")
        try:
            items=tuple(islice(iter(observables),33))
        except TypeError as exc:
            raise ValueError("expected an ordered iterable of observables") from exc
        if not items or len(items)>32:
            raise ResourceLimit("expectations requires 1..32 observables")
        n=self._r._n
        rows=[]
        labels=set()
        for item in items:
            if isinstance(item,Observable):
                terms=item.to_dict(n)
            else:
                label=_pauli_label(n,item)
                if not isinstance(label,str) or len(label)!=n or any(p not in "IXYZ" for p in label):
                    raise ValueError("expected a full-width uppercase I/X/Y/Z Pauli label")
                terms={label:1.0}
            row=tuple(terms.items())
            rows.append(row)
            labels.update(terms)
        if len(labels)*self._r._data.size>work:
            raise ResourceLimit("grouped expectation work exceeds Pauli-state entry budget")
        cache=self._native_pauli_values(sorted(labels))
        values=tuple(math.fsum(coefficient*cache[label] for label,coefficient in row) for row in rows)
        if not all(math.isfinite(value) for value in values):
            raise ArithmeticError("observable expectation is not finite")
        return values

    def probabilities(self, *, bits=None, max_outcomes=65536):
        """All or selected basis probabilities, without an implicit rerun."""
        cap=_int(max_outcomes,1)
        if bits is not None:
            from collections.abc import Mapping
            from itertools import islice
            if isinstance(bits,(str,bytes,Mapping,set,frozenset)):
                raise ValueError("expected ordered basis labels")
            try:
                labels=tuple(islice(iter(bits),min(cap,65536)+1))
            except TypeError as exc:
                raise ValueError("expected ordered basis labels") from exc
            if not 1<=len(labels)<=min(cap,65536):
                raise ResourceLimit("selected probability query exceeds outcome limit")
            if any(not isinstance(label,str) or len(label)!=self._r._n or set(label)-{"0","1"}
                   for label in labels) or len(set(labels))!=len(labels):
                raise ValueError("expected distinct valid basis labels")
            data,norm=self._r._data,self._r._norm_sq
            return {label:float(abs(complex(data[int(label,2)]))**2/norm) for label in labels}
        if self._r._data.size>cap:
            raise ResourceLimit("probability dictionary exceeds outcome limit")
        p=np.abs(self._r._data)
        np.square(p,out=p)
        p/=self._r._norm_sq
        return {format(i,f"0{self._r._n}b"):float(v) for i,v in enumerate(p)}

    def marginal_probabilities(self,wires,*,max_outcomes=65536):
        """Z-basis probabilities; output labels follow the given wire order.

        For wires=[2,0], label "10" denotes q2=1 and q0=0.
        """
        from itertools import islice
        n=self._r._n
        wires=tuple(_int(i) for i in islice(iter(wires),n+1))
        if not wires or len(set(wires))!=len(wires) or any(i>=n for i in wires):
            raise ValueError("invalid marginal wires")
        if (1<<len(wires))>_int(max_outcomes,1):
            raise ResourceLimit("marginal dictionary exceeds outcome limit")
        p=np.abs(self._r._data)
        np.square(p,out=p)
        p/=self._r._norm_sq
        p=p.reshape((2,)*n)
        axes=[n-1-i for i in wires]
        rest=[i for i in range(n) if i not in axes]
        marginal=p.transpose(axes+rest).reshape(1<<len(wires),-1).sum(axis=1)
        return {format(i,f"0{len(wires)}b"):float(v) for i,v in enumerate(marginal)}

    def density_matrix(self, wires=None, *, max_bytes=64*1024**2):
        """Reduced density matrix; first supplied wire is the high-order axis."""
        from itertools import islice
        n=self._r._n
        selected=tuple(range(n-1,-1,-1)) if wires is None else tuple(_int(w) for w in islice(iter(wires),n+1))
        if not selected or len(set(selected))!=len(selected) or any(w>=n for w in selected):
            raise ValueError("invalid density matrix wires")
        # Bound state-sized input and dense output payloads separately.
        _limit(n,budget=max_bytes)
        _limit(2*len(selected),budget=max_bytes)
        axes=[n-1-w for w in selected]
        rest=[i for i in range(n) if i not in axes]
        a=self._r._data.reshape((2,)*n).transpose(axes+rest).reshape(1<<len(selected),-1)
        return (a@a.conj().T)/self._r._norm_sq

    def purity(self, wires=None, *, max_bytes=64*1024**2):
        _int(max_bytes,1)
        if wires is None:
            return 1.0
        rho=self.density_matrix(wires,max_bytes=max_bytes)
        return float(np.clip(np.vdot(rho,rho).real,0,1))

    def conditional_probability(self, event, given):
        """P(event | given) over partial wire->bit assignments."""
        from collections.abc import Mapping
        def validated(mapping):
            if not isinstance(mapping,Mapping) or len(mapping)>self._r._n:
                raise ValueError("expected bounded wire-to-bit mapping")
            result={}
            for wire,bit in mapping.items():
                w,b=_int(wire),_int(bit)
                if w>=self._r._n or b not in (0,1):
                    raise ValueError("invalid wire or bit")
                result[w]=b
            return result
        e,g=validated(event),validated(given)
        def mass(mapping):
            if not mapping:
                return 1.0
            axis=[slice(None)]*self._r._n
            for w,b in mapping.items():
                axis[self._r._n-1-w]=b
            data=self._r._data.reshape((2,)*self._r._n)[tuple(axis)].ravel()
            return float(np.vdot(data,data).real/self._r._norm_sq)
        denominator=mass(g)
        if denominator<=0:
            raise ValueError("conditioning event has zero probability")
        if any(w in g and g[w]!=b for w,b in e.items()):
            return 0.0
        return float(np.clip(mass(g|e)/denominator,0,1))

    def schmidt(self, wires, *, max_rank=256, max_bytes=64*1024**2):
        """Normalized Schmidt singular values across selected/rest partition."""
        from itertools import islice
        n=self._r._n
        selected=tuple(_int(w) for w in islice(iter(wires),n+1))
        if not selected or len(selected)>=n or len(set(selected))!=len(selected) or any(w>=n for w in selected):
            raise ValueError("expected nonempty proper wire subset")
        if (1<<min(len(selected),n-len(selected)))>_int(max_rank,1):
            raise ResourceLimit("Schmidt rank bound exceeded")
        _limit(n,budget=max_bytes)
        axes=[n-1-w for w in selected]
        rest=[i for i in range(n) if i not in axes]
        matrix=self._r._data.reshape((2,)*n).transpose(axes+rest).reshape(1<<len(selected),-1)
        return np.linalg.svd(matrix,compute_uv=False)/math.sqrt(self._r._norm_sq)

    def trace_distance(self,target):
        """Trace distance between normalized pure-state density operators."""
        return math.sqrt(max(0.0,1-self.fidelity(target)))

    def top_probabilities(self, *, k=8):
        """Bounded output, deterministic ties by ascending basis index."""
        import heapq
        k=_int(k,1)
        if k>65536:
            raise ResourceLimit("top-k output limit exceeded")
        data=self._r._data
        if len(data)>=1024 and 8<=k<=32:
            ranked=_topk_exact_chunks(data,k)
        else:
            ranked=heapq.nlargest(min(k,len(data)),range(len(data)),key=lambda i:(abs(data[i])**2,-i))
        return {format(i,f"0{self._r._n}b"):float(abs(data[i])**2/self._r._norm_sq) for i in ranked}

    def observable(self, terms):
        """Expectation of a bounded real linear combination of full-width Paulis."""
        from collections.abc import Mapping
        from ._observable import Observable
        if isinstance(terms,Observable):
            terms=terms.to_dict(self._r._n)
        if not isinstance(terms,Mapping) or not 1<=len(terms)<=256:
            raise ValueError("expected 1..256 Pauli terms")
        # Native Statevector is a call-local read-only handle over the same
        # immutable snapshot. Reuse it for ordinary labels; preserve the
        # legacy dispatch for non-string keys and validation/evaluation order.
        from qiskit.quantum_info import Statevector
        n=self._r._n
        state=None
        def contributions():
            nonlocal state
            for label,coefficient in terms.items():
                numeric=_real(coefficient)
                if type(label) is not str:
                    yield numeric*self.expectation(label)
                    continue
                if len(label)!=n or any(p not in "IXYZ" for p in label):
                    raise ValueError("expected a full-width uppercase I/X/Y/Z Pauli label")
                if state is None:
                    state=Statevector(self._r._data)
                yield numeric*self._native_pauli_value(state,label)
        value=math.fsum(contributions())
        if not math.isfinite(value):
            raise ArithmeticError("observable expectation is not finite")
        return value

    def observable_variance(self, terms, *, max_bytes=64*1024**2):
        """Variance of a real weighted Pauli sum using a bounded native matrix."""
        from collections.abc import Mapping
        from qiskit.quantum_info import SparsePauliOp
        from ._observable import Observable
        if isinstance(terms,Observable):
            terms=terms.to_dict(self._r._n)
        if not isinstance(terms,Mapping) or not 1<=len(terms)<=256:
            raise ValueError("expected 1..256 Pauli terms")
        n=self._r._n
        # Dense matrix payload only, not total RSS; use an eight-wire hard cap.
        if n>8:
            raise ResourceLimit("observable variance limited to eight wires")
        _limit(2*n,budget=max_bytes)
        _limit(n,budget=max_bytes)
        validated=[]
        for label,coefficient in terms.items():
            if type(label) is not str or len(label)!=n or set(label)-set("IXYZ"):
                raise ValueError("invalid Pauli label")
            numeric=_real(coefficient)
            # Var(H + aI) = Var(H). Validate a first, then remove the
            # identity offset before any floating-point matrix/state action.
            if label!="I"*n:
                validated.append((label,numeric))
        if not validated:
            return 0.0
        operator=SparsePauliOp.from_list(validated).to_matrix()
        state=self._r._data/math.sqrt(self._r._norm_sq)
        transformed=operator@state
        mean=np.vdot(state,transformed)
        delta=transformed-mean*state
        value=float(np.vdot(delta,delta).real)
        if not math.isfinite(value):
            raise ArithmeticError("observable variance is not finite")
        return value

    def observable_variance_streamed(self,terms,*,max_bytes=64*1024**2,max_work=1<<25):
        """Apply native Pauli terms to one snapshot without dense operators."""
        from collections.abc import Mapping
        from qiskit.quantum_info import Statevector
        from ._observable import Observable
        if isinstance(terms,Observable):
            terms=terms.to_dict(self._r._n)
        if not isinstance(terms,Mapping) or not 1<=len(terms)<=256:
            raise ValueError("expected 1..256 Pauli terms")
        n=self._r._n
        _limit(n,4,budget=max_bytes)
        if len(terms)*n*self._r._data.size>_int(max_work,1):
            raise ResourceLimit("Pauli application work limit exceeded")
        validated=[]
        for label,coefficient in terms.items():
            if type(label) is not str or len(label)!=n or set(label)-set("IXYZ"):
                raise ValueError("invalid Pauli label")
            numeric=_real(coefficient)
            # Var(H + aI) = Var(H). Validate a first, then remove the
            # identity offset before any floating-point matrix/state action.
            if label!="I"*n:
                validated.append((label,numeric))
        if not validated:
            return 0.0
        state=self._r._data/math.sqrt(self._r._norm_sq)
        result=np.zeros_like(state)
        # Retain the existing four-state payload admission and work cap.
        # The two retained arrays plus conservative chunk scratch must fit
        # that payload budget; scratch is not an RSS guarantee.
        chunk=min(state.size,4096,(_int(max_bytes,1)-32*state.size)//96)
        if chunk:
            _accumulate_pauli_chunks(state,result,validated,chunk)
        else:
            # At the smallest admissible budget the old one-wire path fits
            # the established contract; never reject previously valid input.
            from qiskit.circuit.library import XGate,YGate,ZGate
            gates={"X":XGate(),"Y":YGate(),"Z":ZGate()}
            for label,coefficient in validated:
                term=Statevector(state)
                for wire,axis in enumerate(reversed(label)):
                    if axis!="I":
                        term=term.evolve(gates[axis],qargs=[wire])
                result+=coefficient*term.data
        delta=result-np.vdot(state,result)*state
        value=float(np.vdot(delta,delta).real)
        if not math.isfinite(value):
            raise ArithmeticError("observable variance is not finite")
        return value

    def variance(self,pauli):
        """Pauli variance or bounded streamed variance of a real Pauli sum."""
        from ._observable import Observable
        if isinstance(pauli,Observable):
            return self.observable_variance_streamed(pauli)
        expectation=self.expectation(pauli)
        return max(0.0,1-expectation**2)

    def dirac(self, *, max_terms=16, atol=1e-12):
        """Return first non-negligible amplitudes, with explicit truncation."""
        cap=_int(max_terms,1)
        tolerance=_tol(atol)
        rows=[]
        for i,a in enumerate(self._r._data):
            if abs(a)>tolerance:
                if len(rows)==cap:
                    rows.append("...")
                    break
                rows.append(f"({a.real:.8g}{a.imag:+.8g}j)|{i:0{self._r._n}b}>")
        return " + ".join(rows) if rows else "no terms above tolerance"

    def fidelity(self, target):
        other = target if isinstance(target,Result) else Result(target)
        if other._data.shape != self._r._data.shape:
            raise ValueError("dimension mismatch")
        denominator=other._norm_sq*self._r._norm_sq
        return float(np.clip(abs(np.vdot(other._data,self._r._data))**2/denominator,0,1))

    def norm(self):
        return float(np.linalg.norm(self._r._data))

    def entropy(self, partition, *, max_rank=256, max_bytes=64*1024**2):
        # Pure-state bipartite entanglement entropy, q0 is LSB.
        from itertools import islice
        n = self._r._n
        left,right = (tuple(_int(i) for i in islice(iter(side),n+1)) for side in islice(iter(partition),3))
        if not left or not right or len(left)+len(right)!=n or set(left+right)!=set(range(n)):
            raise ValueError("partition must cover each qubit exactly once")
        if (1<<min(len(left),len(right)))>_int(max_rank,1):
            raise ResourceLimit("Schmidt matrix rank bound exceeds limit")
        _limit(n,budget=max_bytes)
        axes = [n-1-i for i in left+right]
        matrix = self._r._data.reshape((2,)*n).transpose(axes).reshape(2**len(left),-1)
        p = np.linalg.svd(matrix,compute_uv=False)**2
        p = p[p>0]
        p /= p.sum()
        return float(-np.sum(p*np.log2(p)))

class _Checks:
    def __init__(self,result):
        self._r=result

    def normalized(self, *, atol=1e-9):
        t=_tol(atol)
        a=self._r.math.norm()
        return CheckResult("PASS" if abs(a-1)<=t else "FAIL",a,1,t)

    def probability(self,bits,expected,*,atol=1e-9):
        t=_tol(atol)
        expected=_real(expected)
        if not math.isfinite(expected) or not 0<=expected<=1:
            raise ValueError("invalid probability")
        a=self._r.math.probability(bits)
        return CheckResult("PASS" if abs(a-expected)<=t else "FAIL",a,expected,t)

    def fidelity(self,target,*,minimum=1-1e-9):
        minimum=_real(minimum)
        if not math.isfinite(minimum) or not 0<=minimum<=1:
            raise ValueError("invalid minimum")
        a=self._r.math.fidelity(target)
        return CheckResult("PASS" if a>=minimum else "FAIL",a,minimum,0)

    def entangled(self,*,partition,atol=1e-9,max_rank=256,max_bytes=64*1024**2):
        t=_tol(atol)
        a=self._r.math.entropy(partition,max_rank=max_rank,max_bytes=max_bytes)
        return CheckResult("PASS" if a>t else "FAIL",a,t,t)

    def distribution(self,target,*,atol=1e-9):
        """Total variation distance between ideal Z-basis distributions."""
        t=_tol(atol)
        if not isinstance(target,Result):
            raise TypeError("expected Result")
        if target.num_qubits!=self._r.num_qubits:
            raise ValueError("dimension mismatch")
        p=np.abs(self._r._data)
        np.square(p,out=p)
        q=np.abs(target._data)
        np.square(q,out=q)
        # Both arrays are fresh real buffers; retain the original
        # normalization/reduction order without state-sized temporaries.
        p/=p.sum()
        q/=q.sum()
        p-=q
        np.abs(p,out=p)
        distance=float(.5*np.sum(p))
        return CheckResult("PASS" if distance<=t else "FAIL",distance,0,t,"total variation distance")

    def expectation(self,pauli,expected,*,atol=1e-9):
        t=_tol(atol)
        expected=_real(expected)
        from ._observable import Observable
        if not isinstance(pauli,Observable) and not -1<=expected<=1:
            raise ValueError("expected Pauli value must be in [-1,1]")
        a=self._r.math.expectation(pauli)
        detail=f"Observable {pauli.to_dict(self._r.num_qubits)}" if isinstance(pauli,Observable) else f"Pauli {pauli}"
        return CheckResult("PASS" if abs(a-expected)<=t else "FAIL",a,expected,t,detail)

    def expectations(self,values,*,atol=1e-9):
        from ._contracts import Contract
        return Contract(self._r.num_qubits,expectations=values,atol=atol).verify(self._r)

    def state(self,target,*,ignore_global_phase=True,atol=1e-9):
        """Maximum amplitude residual after optional phase alignment."""
        # Reject invalid controls before converting a caller-owned target.
        t=_tol(atol)
        if type(ignore_global_phase) is not bool:
            raise ValueError("ignore_global_phase must be bool")
        other=target if isinstance(target,Result) else Result(target)
        return _residual(self._r._data,other._data,ignore_global_phase,t)
