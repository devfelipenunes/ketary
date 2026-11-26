"""Independent result snapshots and mathematical checks."""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from ._validation import _int, _tol, ResourceLimit

@dataclass(frozen=True)
class CheckResult:
    status: str
    actual: float | None
    expected: float | None
    tolerance: float
    detail: str = ""

    def require(self):
        if self.status != "PASS":
            raise AssertionError(f"{self.status}: actual={self.actual}, expected={self.expected}, tolerance={self.tolerance}; {self.detail}")
        return self

    def __bool__(self):
        raise TypeError("use .status or .require()")

class Result:
    """Independent ideal pure-state snapshot; no circuit reference or re-execution."""

    def __init__(self, amplitudes):
        a = np.asarray(amplitudes, dtype=np.complex128)
        if a.ndim != 1 or a.size < 2 or a.size & (a.size-1):
            raise ValueError("state must have dimension 2**n, n>=1")
        if not np.isfinite(a).all() or not np.isclose(np.vdot(a,a).real,1,rtol=0,atol=1e-9):
            raise ValueError("state must be finite and normalized")
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

    def sample(self, *, shots, seed=None, max_outcomes=65536):
        shots = _int(shots,1)
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

    def statevector(self):
        return self._r._data.copy()

    def amplitude(self,bits):
        """Amplitude of a computational basis ket, in q[n-1]...q[0] order."""
        if not isinstance(bits,str) or len(bits)!=self._r._n or any(b not in "01" for b in bits):
            raise ValueError("invalid bit string")
        return complex(self._r._data[int(bits,2)])

    def probability(self,bits):
        return float(abs(self.amplitude(bits))**2)

    def explain_probability(self,bits):
        """Deterministic, numerical Born-rule explanation, not symbolic proof."""
        a=self.amplitude(bits)
        p=self.probability(bits)
        return f"p(|{bits}>) = |{a.real:.12g}{a.imag:+.12g}j|^2 = {p:.12g}"

    def expectation(self,pauli):
        """Expectation of a Hermitian Pauli string, leftmost character is q[n-1]."""
        if not isinstance(pauli,str) or len(pauli)!=self._r._n or any(p not in "IXYZ" for p in pauli):
            raise ValueError("expected a full-width uppercase I/X/Y/Z Pauli label")
        from qiskit.quantum_info import Pauli, Statevector
        # Native Pauli evaluation operates on the snapshot, not a dense operator.
        value=complex(Statevector(self._r._data).expectation_value(Pauli(pauli)))
        if abs(value.imag)>1e-9 or not math.isfinite(value.real):
            raise ArithmeticError("invalid Hermitian Pauli expectation")
        return float(value.real)

    def probabilities(self, *, max_outcomes=65536):
        if self._r._data.size>_int(max_outcomes,1):
            raise ResourceLimit("probability dictionary exceeds outcome limit")
        return {format(i,f"0{self._r._n}b"):float(p) for i,p in enumerate(np.abs(self._r._data)**2)}

    def marginal_probabilities(self,wires,*,max_outcomes=65536):
        """Z-basis probabilities; output labels follow the given wire order.

        For wires=[2,0], label "10" denotes q2=1 and q0=0.
        """
        wires=tuple(_int(i) for i in wires)
        n=self._r._n
        if not wires or len(set(wires))!=len(wires) or any(i>=n for i in wires):
            raise ValueError("invalid marginal wires")
        if (1<<len(wires))>_int(max_outcomes,1):
            raise ResourceLimit("marginal dictionary exceeds outcome limit")
        p=(np.abs(self._r._data)**2).reshape((2,)*n)
        axes=[n-1-i for i in wires]
        rest=[i for i in range(n) if i not in axes]
        marginal=p.transpose(axes+rest).reshape(1<<len(wires),-1).sum(axis=1)
        return {format(i,f"0{len(wires)}b"):float(v) for i,v in enumerate(marginal)}

    def fidelity(self, target):
        other = target if isinstance(target,Result) else Result(target)
        if other._data.shape != self._r._data.shape:
            raise ValueError("dimension mismatch")
        denominator=np.vdot(other._data,other._data).real*np.vdot(self._r._data,self._r._data).real
        return float(np.clip(abs(np.vdot(other._data,self._r._data))**2/denominator,0,1))

    def norm(self):
        return float(np.linalg.norm(self._r._data))

    def entropy(self, partition):
        # Pure-state bipartite entanglement entropy, q0 is LSB.
        left,right = (tuple(_int(i) for i in side) for side in partition)
        n = self._r._n
        if not left or not right or len(left)+len(right)!=n or set(left+right)!=set(range(n)):
            raise ValueError("partition must cover each qubit exactly once")
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
        expected=float(expected)
        if not math.isfinite(expected) or not 0<=expected<=1:
            raise ValueError("invalid probability")
        a=self._r.math.probability(bits)
        return CheckResult("PASS" if abs(a-expected)<=t else "FAIL",a,expected,t)

    def fidelity(self,target,*,minimum=1-1e-9):
        minimum=float(minimum)
        if not math.isfinite(minimum) or not 0<=minimum<=1:
            raise ValueError("invalid minimum")
        a=self._r.math.fidelity(target)
        return CheckResult("PASS" if a>=minimum else "FAIL",a,minimum,0)

    def entangled(self,*,partition,atol=1e-9):
        t=_tol(atol)
        a=self._r.math.entropy(partition)
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
        expected=float(expected)
        if not math.isfinite(expected) or not -1<=expected<=1:
            raise ValueError("expected Pauli value must be in [-1,1]")
        a=self._r.math.expectation(pauli)
        return CheckResult("PASS" if abs(a-expected)<=t else "FAIL",a,expected,t,f"Pauli {pauli}")

    def state(self,target,*,ignore_global_phase=True,atol=1e-9):
        """Maximum amplitude residual after optional phase alignment."""
        from ._checks import _residual
        other=target if isinstance(target,Result) else Result(target)
        return _residual(self._r._data,other._data,ignore_global_phase,atol)
