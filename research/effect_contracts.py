"""Research-only bounded numerical effect obligations; not formal proofs."""
from dataclasses import dataclass
import hashlib
import json
import math

import numpy as np

MAX_DIM = 32
MAX_KRAUS = 16
ADMISSION_ATOL = 1e-12


def _matrix(a, name, dim=None):
    # Reject before conversion; caller-owned ndarray only, no unbounded iterables.
    if not isinstance(a, np.ndarray) or a.ndim != 2:
        raise TypeError(f"{name}: expected a two-dimensional ndarray")
    n, m = a.shape
    if n != m or n < 2 or n > MAX_DIM or n & (n-1) or (dim is not None and n != dim):
        raise ValueError(f"{name}: expected square power-of-two dimension 2..{MAX_DIM}")
    if a.dtype.kind not in "fiuc":
        raise TypeError(f"{name}: expected numeric dtype")
    b = np.array(a, dtype=np.complex128, order="C", copy=True)
    if not np.isfinite(b).all():
        raise ValueError(f"{name}: nonfinite value")
    return b


def _norm(a):
    return float(np.linalg.norm(a, ord=2))


def _effect(a, name, dim=None):
    b = _matrix(a,name,dim)
    if _norm(b-b.conj().T) > ADMISSION_ATOL:
        raise ValueError(f"{name}: not Hermitian")
    h = (b+b.conj().T)/2
    eig = np.linalg.eigvalsh(h)
    if eig[0] < -ADMISSION_ATOL or eig[-1] > 1+ADMISSION_ATOL:
        raise ValueError(f"{name}: not an effect (0 <= E <= I)")
    return h, _norm(b-h)


def _kraus(values, dim):
    if not isinstance(values,(tuple,list)) or not 1 <= len(values) <= MAX_KRAUS:
        raise ValueError("Kraus: expected bounded list/tuple of 1..16 matrices")
    k = tuple(_matrix(a,"Kraus",dim) for a in values)
    total = sum((a.conj().T@a for a in k), np.zeros((dim,dim),complex))
    defect = _norm(total-np.eye(dim))
    if not math.isfinite(defect) or defect > ADMISSION_ATOL:
        raise ValueError("Kraus: trace-preservation residual exceeds admission tolerance")
    return k, defect


def _hash(matrices):
    h = hashlib.sha256()
    h.update(f"{len(matrices)};".encode())
    for m in matrices:
        h.update(f"{m.shape};".encode())
        h.update(np.ascontiguousarray(m,dtype="<c16").tobytes())
    return h.hexdigest()


def _tol(value):
    if isinstance(value,(bool,np.bool_)) or not isinstance(value,(int,float,np.integer,np.floating)):
        raise ValueError("atol must be finite real in [0,1e-6]")
    t=float(value)
    if not math.isfinite(t) or not 0 <= t <= 1e-6:
        raise ValueError("atol must be finite real in [0,1e-6]")
    return t


@dataclass(frozen=True)
class EffectReport:
    status: str
    scope: str
    dim: int
    atol: float
    max_residual: float
    spectral_residual: float
    trace_preservation_residual: float
    effect_symmetrization_residual: float
    numerical_guard: float
    specification_sha256: str
    channel_sha256: str
    witness: tuple[tuple[float,float], ...] | None
    witness_gap: float | None

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)

    def require(self):
        if self.status != "PASS":
            raise AssertionError(f"{self.status}: max residual={self.max_residual}; atol={self.atol}")
        return self


def _evaluate(a,b,k,defect,sym,tol):
    # Positive effects and TP are numerical admission checks, not exact proofs.
    adj = sum((x.conj().T@b@x for x in k), np.zeros_like(a))
    m = a-adj
    m = (m+m.conj().T)/2
    vals,vecs = np.linalg.eigh(m)
    top = float(vals[-1])
    v = vecs[:,-1]
    resid = float(np.linalg.norm(m@v-top*v))
    gap = float(np.vdot(v,a@v).real -
                sum(np.vdot(x@v,b@(x@v)).real for x in k))
    # Deliberately conservative diagnostic gray band; not a certified error bound.
    guard = max(ADMISSION_ATOL, 8*resid, 8*defect, 8*sym)
    if top > tol+guard and gap > tol+guard:
        status="FAIL"
        witness=tuple((float(z.real),float(z.imag)) for z in v)
        witness_gap=gap
    elif top < tol-guard:
        status="PASS"
        witness=None
        witness_gap=None
    else:
        status="INCONCLUSIVE"
        witness=None
        witness_gap=None
    return EffectReport(status,"numerical effect inequality over all input density matrices; not formal proof",
                        a.shape[0],tol,top,resid,defect,sym,guard,
                        _hash((a,b)),_hash(k),witness,witness_gap)


def verify_effect(pre, post, kraus, *, atol=1e-9):
    """Evaluate A <= E*(B) + atol I in a bounded admitted numerical model."""
    tol = _tol(atol)
    a,sa = _effect(pre,"pre")
    b,sb = _effect(post,"post",a.shape[0])
    k,defect = _kraus(kraus,a.shape[0])
    return _evaluate(a,b,k,defect,max(sa,sb),tol)


def verify_circuit(circuit, pre, post, *, atol=1e-9):
    """Explicit adapter, Qiskit Operator is authoritative for admitted unitary circuit."""
    import ketary as q
    from qiskit.quantum_info import Operator
    if not isinstance(circuit,q.Circuit):
        raise TypeError("expected Ketary Circuit")
    if not 1 <= circuit.num_qubits <= 5:
        raise ValueError("effect prototype limited to 1..5 qubits")
    # Validate specification before native matrix creation.
    dim=1<<circuit.num_qubits
    _tol(atol)
    _effect(pre,"pre",dim)
    _effect(post,"post",dim)
    native=circuit.to_qiskit()
    if len(native.data)>256 or native.num_parameters or native.num_clbits:
        raise ValueError("expected bound unitary circuit, at most 256 instructions")
    return verify_effect(pre,post,(Operator(native).data,),atol=atol)


def verify_sequence(pre, middle, post, first, second, *, atol=1e-9):
    """Check local obligations and independently evaluate the composite.
    
    Same square dimension throughout; at most 16 composite Kraus matrices.
    No inferred PASS from component reports or unchecked approximate TP.
    """
    t=_tol(atol)
    if 2*t>1e-6:
        raise ValueError("combined tolerance exceeds prototype cap")
    a,sa=_effect(pre,"pre")
    r,sr=_effect(middle,"middle",a.shape[0])
    b,sb=_effect(post,"post",a.shape[0])
    k,dk=_kraus(first,a.shape[0])
    l,dl=_kraus(second,a.shape[0])
    if len(k)*len(l)>MAX_KRAUS:
        raise ValueError("composite Kraus count exceeds 16")
    p=_evaluate(a,r,k,dk,max(sa,sr),t)
    q=_evaluate(r,b,l,dl,max(sr,sb),t)
    composite=tuple(y@x for y in l for x in k)
    direct=verify_effect(a,b,composite,atol=2*t)
    return {"first":p.to_dict(),"second":q.to_dict(),"direct":direct.to_dict(),
            "scope":"direct composed numerical check; local PASS not a formal compositional certificate"}


def projector(v):
    if not isinstance(v,np.ndarray) or v.ndim!=1 or not 2<=len(v)<=MAX_DIM or len(v)&(len(v)-1):
        raise ValueError("expected bounded power-of-two state vector")
    x=np.asarray(v,dtype=complex)
    if not np.isfinite(x).all() or abs(np.vdot(x,x).real-1)>ADMISSION_ATOL:
        raise ValueError("expected normalized finite state")
    return np.outer(x,x.conj())


def demo():
    import ketary as q
    zero=projector(np.array([1,0,0,0]))
    plus=projector(np.array([1,0,0,1])/np.sqrt(2))
    good=q.bell()
    bad=good.copy().z(0)
    # Existing snapshot Contract remains a separate, useful obligation.
    contract=q.Contract(2,probabilities={"00":.5,"11":.5},expectations={"XX":1})
    out={}
    for name,c in (("bell",good),("relative_phase_mutant",bad)):
        out[name]={"snapshot":contract.verify(c.run()).to_dict(),
                   "effect":verify_circuit(c,zero,plus).to_dict()}
    return out


if __name__=="__main__":
    print(json.dumps(demo(),indent=2,allow_nan=False))
