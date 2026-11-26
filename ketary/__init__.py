"""Experimental Ketary SDK spike. Not a stable API."""
from __future__ import annotations
from dataclasses import dataclass
import math
import operator
import numpy as np

class UnsupportedOperation(ValueError):
    pass

class ResourceLimit(ValueError):
    pass

def _int(value, minimum=0):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError("expected an integer, not bool")
    try:
        value = operator.index(value)
    except TypeError as exc:
        raise ValueError("expected an integer") from exc
    if value < minimum:
        raise ValueError(f"expected integer >= {minimum}")
    return value

def _sdk():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    return QuantumCircuit, Statevector

def _limit(n, snapshots=1, budget=64*1024**2):
    budget = _int(budget, 1)
    # Payload only; not a guarantee of total process RSS.
    if n > 62 or 16 * (1 << n) * snapshots > budget:
        raise ResourceLimit("dense statevector payload exceeds budget")

def _tol(value):
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError("invalid tolerance")
    return value

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

@dataclass(frozen=True)
class TraceStep:
    operation: str
    wires: tuple[int,...]
    result: Result

class Circuit:
    """One builder, one authoritative Qiskit circuit (strict PoC subset)."""

    def __init__(self,n):
        QC,_=_sdk()
        self._qc=QC(_int(n,1))

    @property
    def gates(self):
        return _Gates(self)

    @property
    def debug(self):
        return _Debug(self)

    def analyze(self):
        return self.run()

    @property
    def num_qubits(self):
        return self._qc.num_qubits

    @classmethod
    def _from_native(cls,qc,*,owned=False):
        _validate(qc)
        c=cls.__new__(cls)
        c._qc=qc if owned else qc.copy()
        return c

    def to_qiskit(self):
        return self._qc.copy()

    def compose(self,other,*,wires=None):
        if not isinstance(other,Circuit):
            raise TypeError("expected Circuit")
        indices=list(range(other.num_qubits)) if wires is None else [_int(i) for i in wires]
        if len(indices)!=other.num_qubits or len(set(indices))!=len(indices) or any(i>=self.num_qubits for i in indices):
            raise ValueError("invalid wire mapping")
        return self._from_native(self._qc.compose(other._qc,qubits=indices,inplace=False),owned=True)

    def inverse(self):
        return self._from_native(self._qc.inverse(),owned=True)

    def decompose(self,*,reps=1):
        # Selective SWAP lowering: general decomposition leaves the whitelist.
        return self._from_native(self._qc.decompose(gates_to_decompose=["swap"], reps=_int(reps,1)),owned=True)

    def run(self,*,mode="statevector",max_bytes=64*1024**2):
        if mode!="statevector":
            raise UnsupportedOperation("only ideal statevector in PoC")
        _limit(self.num_qubits,budget=max_bytes)
        _,SV=_sdk()
        return Result(SV.from_instruction(self._qc).data)

class _Gates:
    def __init__(self,c):
        self._c=c

    def _apply(self,name,*wires):
        indices=tuple(_int(w) for w in wires)
        if len(set(indices))!=len(indices) or any(w>=self._c.num_qubits for w in indices):
            raise ValueError("invalid wires")
        getattr(self._c._qc,name)(*indices)
        return self._c

    def h(self,q):
        return self._apply("h",q)

    def x(self,q):
        return self._apply("x",q)

    def z(self,q):
        return self._apply("z",q)

    def cx(self,c,t):
        return self._apply("cx",c,t)

    def swap(self,a,b):
        return self._apply("swap",a,b)

def _validate(qc):
    QC,_=_sdk()
    from qiskit.circuit.library import HGate,XGate,ZGate,CXGate,SwapGate
    if not isinstance(qc,QC):
        raise TypeError("expected QuantumCircuit")
    if qc.num_qubits<1 or qc.num_clbits or qc.parameters or getattr(qc,"layout",None) is not None or qc.metadata:
        raise UnsupportedOperation("PoC supports only unparameterized logical quantum circuits without metadata/classical bits/layout")
    allowed=(HGate,XGate,ZGate,CXGate,SwapGate)
    for item in qc.data:
        if item.operation.base_class not in allowed or item.operation.params or item.clbits:
            raise UnsupportedOperation(f"unsupported operation: {item.operation.name}")
        if item.operation.base_class is CXGate and item.operation.ctrl_state != 1:
            raise UnsupportedOperation("open-control CX is outside the PoC whitelist")
    if not math.isfinite(float(qc.global_phase)):
        raise ValueError("invalid global phase")

class _Debug:
    def __init__(self,c):
        self._c=c

    def trace(self,*,max_bytes=64*1024**2,max_steps=256):
        qc=self._c._qc
        if qc.num_qubits > 8:
            raise ResourceLimit("trace supports at most eight qubits in PoC")
        if len(qc.data)>_int(max_steps):
            raise ResourceLimit("trace step limit exceeded")
        _limit(qc.num_qubits,len(qc.data)+1,budget=max_bytes)
        _,SV=_sdk()
        a=np.zeros(1<<qc.num_qubits,dtype=complex)
        a[0]=np.exp(1j*float(qc.global_phase))
        state=SV(a)
        steps=[TraceStep("initial (global phase applied)",(),Result(state.data))]
        for item in qc.data:
            wires=tuple(qc.find_bit(w).index for w in item.qubits)
            state=state.evolve(item.operation,qargs=list(wires))
            steps.append(TraceStep(item.operation.name,wires,Result(state.data)))
        return tuple(steps)

def from_qiskit(qc):
    return Circuit._from_native(qc)

def bell():
    return Circuit(2).gates.h(0).gates.cx(0,1)

def ghz(n):
    n=_int(n,2)
    c=Circuit(n).gates.h(0)
    for i in range(1,n):
        c.gates.cx(i-1,i)
    return c
