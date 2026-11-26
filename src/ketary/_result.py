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

class Result:
    """Independent ideal pure-state snapshot; no circuit reference or re-execution."""

    def __init__(self, amplitudes):
        a = np.asarray(amplitudes, dtype=np.complex128)
        if a.ndim != 1 or a.size < 2 or a.size & (a.size-1):
            raise ValueError("state must have dimension 2**n, n>=1")
        norm_sq=float(np.vdot(a,a).real)
        if not np.isfinite(a).all() or not math.isclose(norm_sq,1,rel_tol=0,abs_tol=1e-9):
            raise ValueError("state must be finite and normalized")
        self._norm_sq = norm_sq
        self._data = a.copy()
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
            probabilities=self.math.marginal_probabilities(wires,max_outcomes=cap)
            if seed is not None:
                seed=_int(seed)
            p=np.array(list(probabilities.values()))
            p/=p.sum()
            counts=np.random.default_rng(seed).multinomial(shots,p)
            return {key:int(v) for key,v in zip(probabilities,counts,strict=True) if v}
        if min(shots,self._data.size)>_int(max_outcomes,1):
            raise ResourceLimit("potential sample dictionary exceeds outcome limit")
        if seed is not None:
            seed = _int(seed)
        p = np.abs(self._data)**2
        p /= p.sum()
        counts = np.random.default_rng(seed).multinomial(shots, p)
        return {format(i,f"0{self._n}b"):int(v) for i,v in enumerate(counts) if v}

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
        from qiskit.quantum_info import Pauli, Statevector
        # Native Pauli evaluation operates on the snapshot, not a dense operator.
        value=complex(Statevector(self._r._data).expectation_value(Pauli(pauli)))
        if abs(value.imag)>1e-9 or not math.isfinite(value.real):
            raise ArithmeticError("invalid Hermitian Pauli expectation")
        return float(np.clip(value.real/self._r._norm_sq,-1,1))

    def probabilities(self, *, max_outcomes=65536):
        if self._r._data.size>_int(max_outcomes,1):
            raise ResourceLimit("probability dictionary exceeds outcome limit")
        return {format(i,f"0{self._r._n}b"):float(p) for i,p in enumerate(np.abs(self._r._data)**2/self._r._norm_sq)}

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
        p=(np.abs(self._r._data)**2/self._r._norm_sq).reshape((2,)*n)
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
        value=math.fsum(_real(coefficient)*self.expectation(label) for label,coefficient in terms.items())
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
            validated.append((label,_real(coefficient)))
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
            validated.append((label,_real(coefficient)))
        # Statevector.evolve(Pauli) is not assumed matrix-free; apply native
        # one-wire gates instead, preserving Y and tensor ordering.
        from qiskit.circuit.library import XGate,YGate,ZGate
        gates={"X":XGate(),"Y":YGate(),"Z":ZGate()}
        state=self._r._data/math.sqrt(self._r._norm_sq)
        result=np.zeros_like(state)
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
        p=np.abs(self._r._data)**2
        q=np.abs(target._data)**2
        distance=float(.5*np.sum(np.abs(p/p.sum()-q/q.sum())))
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
        other=target if isinstance(target,Result) else Result(target)
        return _residual(self._r._data,other._data,ignore_global_phase,atol)
