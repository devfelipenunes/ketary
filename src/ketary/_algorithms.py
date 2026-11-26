"""Small reusable state-preparation factories."""
from __future__ import annotations
from ._circuit import Circuit
from ._validation import _int

def bell():
    return Circuit(2).gates.h(0).gates.cx(0,1)

def ghz(n):
    n=_int(n,2)
    c=Circuit(n).gates.h(0)
    for i in range(1,n):
        c.gates.cx(i-1,i)
    return c


def constant_oracle(n, *, value=0):
    """Construct U_f for f(x)=value, with the target on wire n."""
    n=_int(n,1)
    value=_int(value)
    if value not in (0,1):
        raise ValueError("constant value must be 0 or 1")
    c=Circuit(n+1)
    if value:
        c.gates.x(n)
    return c

def parity_oracle(mask, *, offset=0):
    """Construct U_f for f(x)=a·x XOR offset, a nonzero binary mask.

    The rightmost character denotes input wire zero. Target is wire len(mask).
    """
    if not isinstance(mask,str) or not mask or any(b not in "01" for b in mask) or "1" not in mask:
        raise ValueError("mask must be a nonzero binary string")
    offset=_int(offset)
    if offset not in (0,1):
        raise ValueError("offset must be 0 or 1")
    c=Circuit(len(mask)+1)
    for i,bit in enumerate(reversed(mask)):
        if bit=="1":
            c.gates.cx(i,len(mask))
    if offset:
        c.gates.x(len(mask))
    return c

def deutsch_jozsa(oracle):
    """Build the Deutsch-Jozsa circuit for an explicit bit-flip oracle.

    Caller promises U_f|x,y> = |x,y XOR f(x)> with constant or balanced f.
    The last wire is the target; all lower wires hold the input register.
    This function does not prove the promise or execute the circuit.
    """
    if not isinstance(oracle,Circuit):
        raise TypeError("expected Circuit oracle")
    n=oracle.num_qubits-1
    if n<1:
        raise ValueError("oracle requires at least one input and one target")
    c=Circuit(n+1).gates.x(n)
    for i in range(n+1):
        c.gates.h(i)
    c=c.compose(oracle)
    for i in range(n):
        c.gates.h(i)
    return c


def bernstein_vazirani(mask):
    """Recover a hidden nonzero parity mask using an explicit oracle."""
    return deutsch_jozsa(parity_oracle(mask))


def qft(n, *, inverse=False, swaps=True):
    """Exact logical QFT with positive Fourier sign, highest-wire-first labels."""
    from math import pi
    n=_int(n,1)
    if n>22:
        from ._validation import ResourceLimit
        raise ResourceLimit("QFT construction limited to 22 qubits")
    if type(inverse) is not bool or type(swaps) is not bool:
        raise ValueError("inverse and swaps must be boolean")
    c=Circuit(n)
    for target in reversed(range(n)):
        c.h(target)
        for control in reversed(range(target)):
            c.cp(pi/(2**(target-control)),control,target)
    if swaps:
        for i in range(n//2):
            c.swap(i,n-1-i)
    return c.inverse() if inverse else c


def grover(marked, *, iterations=None):
    """Small pedagogical single-marked-basis search (2 or 3 input qubits)."""
    from math import floor,pi,asin,sqrt
    if type(marked) is not str or len(marked) not in (2,3) or set(marked)-{"0","1"}:
        raise ValueError("expected a 2- or 3-bit marked label")
    n=len(marked)
    count=floor(pi/(4*asin(1/sqrt(2**n)))) if iterations is None else _int(iterations)
    if count>64:
        from ._validation import ResourceLimit
        raise ResourceLimit("Grover iteration limit exceeded")
    c=Circuit(n).h_many(range(n))
    def phase_flip(bits):
        zeros=[i for i,b in enumerate(reversed(bits)) if b=="0"]
        for i in zeros: c.x(i)
        if n==2:
            c.cz(0,1)
        else:
            c.h(2).ccx(0,1,2).h(2)
        for i in zeros: c.x(i)
    for _ in range(count):
        phase_flip(marked)
        c.h_many(range(n))
        phase_flip("0"*n)
        c.h_many(range(n))
        # H(I-2|0><0|)H differs from standard diffusion by global -1.
        c._qc.global_phase += pi
    return c


def superdense(bits):
    """Ideal coherent superdense encoding and decoding; no communication model."""
    if type(bits) is not str or len(bits)!=2 or set(bits)-{"0","1"}:
        raise ValueError("expected two bits")
    c=bell()
    # Z encodes the low-order output bit, X the high-order output bit.
    if bits[0]=="1": c.x(0)
    if bits[1]=="1": c.z(0)
    return c.cx(0,1).h(0)


def phase_estimation(phase, precision=3):
    """QPE for known phase gate P(2*pi*phase), eigenstate |1>.

    This pedagogical circuit is not a generic controlled-unitary synthesis API.
    Counting wires 0..precision-1; eigenstate wire precision.
    """
    from math import pi
    from ._validation import _real,ResourceLimit
    phase=_real(phase)
    precision=_int(precision,1)
    if not 0<=phase<1:
        raise ValueError("phase must be in [0,1)")
    if precision>12:
        raise ResourceLimit("phase estimation precision limited to 12 bits")
    c=Circuit(precision+1).x(precision).h_many(range(precision))
    for wire in range(precision):
        c.cp(2*pi*((phase*(1<<wire))%1),wire,precision)
    return c.compose(qft(precision,inverse=True),wires=range(precision))


def simon(secret):
    """One coherent Simon iteration for a constructed XOR-periodic oracle.

    For nonzero binary s, f(x)=x XOR (x[pivot]*s). The function is exactly
    two-to-one with period s. The caller samples the input wires and solves
    the resulting GF(2) equations; this does not pretend one sample finds s.
    """
    from ._validation import ResourceLimit
    if type(secret) is not str or not secret or set(secret)-{"0","1"} or "1" not in secret:
        raise ValueError("expected nonzero binary secret")
    n=len(secret)
    if n>10:
        raise ResourceLimit("Simon example limited to ten input wires")
    active=[i for i,b in enumerate(reversed(secret)) if b=="1"]
    pivot=active[0]
    c=Circuit(2*n).h_many(range(n))
    for i in range(n):
        if i!=pivot:
            c.cx(i,n+i)
            if i in active:
                c.cx(pivot,n+i)
    return c.h_many(range(n))
