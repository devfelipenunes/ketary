"""Round 18 research-only contracts. Exact and numerical scopes never mix."""
from dataclasses import dataclass
from fractions import Fraction
from math import lcm
from facade17 import signed
from consolidated12 import Engine
from native9 import bounds
from sparse import BudgetExceeded
from engine import product_witness

@dataclass(frozen=True)
class SumReport:
    status: str
    scope: str
    residual: tuple
    witness: object
    work: int

def admit_sum(n, terms):
    if type(terms) is not tuple or not 1 <= len(terms) <= 64:
        raise ValueError("bounded tuple of rational Pauli terms")
    out = {}
    for term in terms:
        if type(term) is not tuple or len(term) != 2:
            raise ValueError("term")
        p, c = term
        if type(c) is not Fraction or max(c.numerator.bit_length(), c.denominator.bit_length()) > 64:
            raise ValueError("bounded rational coefficients")
        x,z,s = signed(p,n)
        key = x,z
        out[key] = out.get(key,Fraction(0)) + (-1 if s else 1)*c
    return {p:c for p,c in out.items() if c}

def exact_sum(engine, pre, post, *, max_terms=4096, max_work=2_000_000):
    """U† B U = A for rational Hermitian Pauli sums, exact Q(sqrt(2)).
    Work counts term admission, native term visits, merges and witness upper bound;
    it is not a bound on wall-clock, allocator bytes or integer bit operations.
    """
    if type(engine) is not Engine: raise TypeError("prepared engine")
    bounds(max_terms,max_work)
    n=engine.session.width
    a,b=admit_sum(n,pre),admit_sum(n,post)
    scope="Exact rational Pauli-sum equality under admitted Clifford+T snapshot"
    work=len(pre)+len(post)
    def inc():
        return SumReport("INCONCLUSIVE",scope,(),None,min(work,max_work))
    if work>max_work or len(a)>max_terms or len(b)>max_terms:return inc()
    d={p:(-c,Fraction(0)) for p,c in a.items()}
    for p,c in sorted(b.items()):
        if work>=max_work:return inc()
        try:
            r=engine.session.propagate((*p,0),max_terms=max_terms,max_work=max_work-work)
        except BudgetExceeded:
            return SumReport("INCONCLUSIVE",scope,(),None,max_work)
        work+=r.work+len(r.terms)
        if work>max_work:return inc()
        for x,z,u,v in r.terms:
            k=x,z; old=d.get(k,(Fraction(0),Fraction(0)))
            value=(old[0]+c*Fraction(u,1<<r.denominator_power),
                   old[1]+c*Fraction(v,1<<r.denominator_power))
            if value==(0,0):d.pop(k,None)
            else:d[k]=value
            if len(d)>max_terms:return inc()
    if not d:return SumReport("PASS",scope,(),None,work)
    # Reserve conservative work for sign conditioning in the existing witness.
    work+=(2*n+3)*len(d)
    if work>max_work:return inc()
    den=lcm(*(f.denominator for pair in d.values() for f in pair))
    w=product_witness(n,{p:tuple(int(f*den) for f in pair) for p,pair in d.items()},0)
    witness=(w.axes,w.signs,tuple(Fraction(v,den) for v in w.numerator))
    return SumReport("FAIL",scope,tuple(sorted(d.items())),witness,work)

def phase_compare(actual, reference, *, tol=1e-10):
    """Independent bounded numerical STRICT unitary comparison. Never use
    phase-insensitive snapshot identity as strict or controlled equivalence."""
    import math
    import numpy as np
    from qiskit.quantum_info import Operator
    if type(tol) is not float or not math.isfinite(tol) or not 0<tol<=1e-6:
        raise ValueError("tolerance")
    if actual.num_qubits!=reference.num_qubits or not 1<=actual.num_qubits<=6:
        raise ValueError("bounded equal widths")
    for c in (actual,reference):
        if c.num_clbits or c.num_parameters or len(c.data)>512:
            raise ValueError("bounded unitary inputs")
    a,b=Operator(actual).data,Operator(reference).data
    if not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError("nonfinite")
    err=float(np.linalg.norm(a-b,ord=2))
    return ("PASS" if err<=tol/10 else "FAIL" if err>=tol*10 else "INCONCLUSIVE",err)

def dense_sum_residual(circuit,pre,post):
    """Independent numerical oracle for small Pauli sums; not a certificate."""
    import numpy as np
    from qiskit.quantum_info import Operator,Pauli
    from benchmark import label
    n=circuit.num_qubits
    if not 1<=n<=6 or len(circuit.data)>512 or circuit.num_clbits or circuit.num_parameters:
        raise ValueError("bounded oracle")
    def matrix(terms):
        return sum((float(c)*Pauli(label(n,(*p,0))).to_matrix()
                    for p,c in admit_sum(n,terms).items()),np.zeros((1<<n,1<<n),complex))
    u=Operator(circuit).data
    return float(np.linalg.norm(u.conj().T@matrix(post)@u-matrix(pre),ord=2))

def z_channel_adjoint(n, p, wire, kind):
    """Exact adjoint on one Pauli: nonselective Z-measurement or reset to |0>.
    None represents the zero operator. No selective measurement or branches."""
    x,z,s=signed(p,n)
    if type(wire) is not int or not 0<=wire<n or kind not in ("measure","reset"):
        raise ValueError("wire/channel")
    bit=1<<wire
    if x&bit:return None
    return x,z&~bit if kind=="reset" else z,s

def syndrome(n, stabilizers, error):
    """Exact commutation syndrome of an independent commuting generator list.
    Does not certify code distance, recovery, or fault tolerance."""
    if type(stabilizers) is not tuple or not 1<=len(stabilizers)<=n:
        raise ValueError("generator list")
    ps=[signed(p,n) for p in stabilizers]
    def parity(a,b):return ((a[0]&b[1]).bit_count()+(a[1]&b[0]).bit_count())%2
    basis={}
    for i,p in enumerate(ps):
        if any(parity(p,q) for q in ps[:i]):raise ValueError("noncommuting generators")
        v=p[0]|(p[1]<<n)
        while v:
            k=v.bit_length()-1
            if k not in basis: basis[k]=v; break
            v^=basis[k]
        if not v:raise ValueError("dependent generators")
    e=signed(error,n)
    return tuple(parity(p,e) for p in ps)

def compose_error_bounds(bounds_):
    """Exact triangle bound for sequential CPTP channel diamond distances
    given externally established upper bounds. Not a verifier of those bounds."""
    if type(bounds_) is not tuple or not 1<=len(bounds_)<=64:
        raise ValueError("bounded stages")
    for x in bounds_:
        if type(x) is not Fraction or not 0<=x<=2 or max(x.numerator.bit_length(),x.denominator.bit_length())>64:
            raise ValueError("diamond norm bound")
    return min(Fraction(2),sum(bounds_,Fraction(0)))
