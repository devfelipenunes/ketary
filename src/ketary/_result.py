"""Independent result snapshots and mathematical checks."""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from ._validation import _int, _tol

@dataclass(frozen=True)
class CheckResult:
    status: str
    actual: float
    expected: float
    tolerance: float

    def require(self):
        if self.status != "PASS":
            raise AssertionError(f"{self.status}: actual={self.actual}, expected={self.expected}, tolerance={self.tolerance}")
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
    def math(self):
        return _Math(self)

    @property
    def test(self):
        return _Checks(self)

    def sample(self, *, shots, seed=None):
        shots = _int(shots,1)
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

    def probabilities(self):
        return {format(i,f"0{self._r._n}b"):float(p) for i,p in enumerate(np.abs(self._r._data)**2)}

    def fidelity(self, target):
        other = target if isinstance(target,Result) else Result(target)
        if other._data.shape != self._r._data.shape:
            raise ValueError("dimension mismatch")
        return float(np.clip(abs(np.vdot(other._data,self._r._data))**2,0,1))

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
        if not isinstance(bits,str) or len(bits)!=self._r._n or any(b not in "01" for b in bits):
            raise ValueError("invalid bit string")
        if not math.isfinite(expected) or not 0<=expected<=1:
            raise ValueError("invalid probability")
        a=float(abs(self._r._data[int(bits,2)])**2)
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
