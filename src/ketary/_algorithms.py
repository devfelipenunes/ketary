"""Small reusable state-preparation factories."""
from __future__ import annotations
from ._circuit import Circuit
from ._validation import _int

def basis(label):
    """Prepare a computational basis label (highest wire first), as a unitary X block."""
    from ._validation import ResourceLimit
    if type(label) is not str or not label:
        raise ValueError("expected a nonempty binary label")
    if len(label)>62:
        raise ResourceLimit("basis preparation supports at most 62 wires")
    if set(label)-{"0","1"}:
        raise ValueError("expected a binary label")
    c=Circuit(len(label))
    active=[i for i,b in enumerate(reversed(label)) if b=="1"]
    return c.x(active) if active else c


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


def teleportation(theta,phi,*,verify=False):
    """Ideal three-wire teleportation with actual measurement and feedforward.

    Prepare RZ(phi) RY(theta)|0> on wire 0. Output wire 2 is measured in
    Z, or after inverse preparation if verify=True. Three classical bits:
    c2=output, c1/c0=Bell measurement outcomes.
    """
    if type(verify) is not bool:
        raise ValueError("verify must be bool")
    from ._validation import _angle
    theta,phi=_angle(theta),_angle(phi)
    c=Circuit.classical(3,3).ry(theta,0).rz(phi,0).h(1).cx(1,2)
    c.cx(0,1).h(0).measure(0,0).measure(1,1)
    c.if_x(2,1).if_z(2,0)
    if verify:
        c.rz(-phi,2).ry(-theta,2)
    return c.measure(2,2)


def recover_simon(samples,n):
    """Recover the unique nonzero binary secret from orthogonal sample labels.

    Returns None for rank below n-1; full rank violates Simon's promise.
    This is bounded classical GF(2) elimination, not circuit execution.
    """
    from itertools import islice
    from ._validation import ResourceLimit
    n=_int(n,1)
    if n>10:
        raise ResourceLimit("Simon recovery limited to ten input bits")
    rows={}
    for k,label in enumerate(islice(iter(samples),4097)):
        if k==4096:
            raise ResourceLimit("Simon sample limit exceeded")
        if type(label) is not str or len(label)!=n or set(label)-{"0","1"}:
            raise ValueError("invalid Simon sample label")
        value=int(label,2)
        while value:
            pivot=value.bit_length()-1
            if pivot in rows:
                value^=rows[pivot]
            else:
                rows[pivot]=value
                break
    if len(rows)==n:
        raise ValueError("samples violate the nonzero-secret promise")
    if len(rows)<n-1:
        return None
    free=next(i for i in range(n) if i not in rows)
    answer=1<<free
    for pivot in sorted(rows):
        if (rows[pivot]&answer).bit_count()%2:
            answer|=1<<pivot
    return format(answer,f"0{n}b")


def _decode_peak(result,wires,atol):
    from ._result import Result
    from ._validation import _tol
    if not isinstance(result,Result):
        raise TypeError("expected ideal Result snapshot")
    tolerance=_tol(atol)
    distribution=result.math.marginal_probabilities(wires)
    peak=max(distribution.values())
    labels=tuple(label for label,p in distribution.items() if peak-p<=tolerance)
    return {"status":"PASS" if len(labels)==1 else "INCONCLUSIVE",
            "label":labels[0] if len(labels)==1 else None,
            "peak_probability":peak,"tied_labels":list(labels),
            "scope":"unique modal ideal outcome only; not proof of algorithm promise"}

def decode_phase_estimation(result,*,precision,atol=1e-9):
    """Decode the modal counting-register outcome for the provided QPE example."""
    from ._result import Result
    from ._validation import ResourceLimit
    p=_int(precision,1)
    if p>12:
        raise ResourceLimit("phase estimation precision limited to 12 bits")
    if not isinstance(result,Result):
        raise TypeError("expected ideal Result snapshot")
    if result.num_qubits!=p+1:
        raise ValueError("expected precision counting wires plus one eigenstate wire")
    report=_decode_peak(result,range(p-1,-1,-1),atol)
    report["phase"]=None if report["label"] is None else int(report["label"],2)/(1<<p)
    from ._reports import PhaseEstimateReport
    return PhaseEstimateReport(report)

def decode_bernstein_vazirani(result,*,atol=1e-9):
    """Decode the modal input label of the documented parity-oracle example."""
    from ._result import Result
    from ._validation import ResourceLimit
    if not isinstance(result,Result):
        raise TypeError("expected ideal Result snapshot")
    n=result.num_qubits-1
    if not 1<=n<=16:
        raise ResourceLimit("decoder supports 1..16 input wires plus target")
    from ._reports import ModalOutcomeReport
    return ModalOutcomeReport(_decode_peak(result,range(n-1,-1,-1),atol))

def decode_teleportation(result):
    """Return empirical output-bit frequencies, not a fidelity estimate."""
    from ._classical import ShotResult
    if not isinstance(result,ShotResult):
        raise TypeError("expected ShotResult")
    if result.num_clbits!=3 or (2 not in result.measured_bits):
        raise ValueError("expected the teleportation example's measured output bit 2")
    shots=_int(result.shots,1)
    counts=result.counts
    if len(counts)!=len(result._counts) or sum(counts.values())!=shots or any(
            type(k) is not str or len(k)!=3 or set(k)-set("01") or type(v) is not int or v<0
            for k,v in counts.items()):
        raise ValueError("invalid shot count schema")
    output={bit:sum(v for k,v in counts.items() if k[0]==bit) for bit in ("0","1")}
    return {"scope":"empirical output bit 2; not state fidelity or proof of teleportation",
            "shots":shots,"counts":output,"probabilities":{k:v/shots for k,v in output.items()}}


def ansatz(n,*,rotations=("ry",),entanglement="linear",reps=1,prefix="theta"):
    """Native alternating rotations/CX ansatz; no execution or optimizer.

    Rotation gate order, parameter order and entanglement semantics are native
    Qiskit n_local. Reusing the same prefix in independent templates is not
    implicit parameter sharing.
    """
    from collections.abc import Mapping
    from itertools import islice
    from ._validation import ResourceLimit
    n,reps=_int(n,2),_int(reps,1)
    if n>62 or reps>64:
        raise ResourceLimit("ansatz limited to 62 wires and 64 repetitions")
    if isinstance(rotations,(str,bytes,set,frozenset,Mapping)):
        raise ValueError("rotations must be an ordered sequence")
    try:
        rotations=tuple(islice(iter(rotations),4))
    except TypeError as exc:
        raise ValueError("rotations must be an ordered sequence") from exc
    if not 1<=len(rotations)<=3 or any(type(g) is not str or g not in ("rx","ry","rz") for g in rotations):
        raise ValueError("expected 1..3 ordered rx/ry/rz rotation blocks")
    if type(entanglement) is not str or entanglement not in ("linear","reverse_linear","circular","full"):
        raise ValueError("unsupported native entanglement topology")
    if type(prefix) is not str or not prefix or len(prefix)>112:
        raise ValueError("expected a nonempty parameter prefix up to 112 characters")
    parameters=n*len(rotations)*(reps+1)
    edges=n*(n-1)//2 if entanglement=="full" else n if entanglement=="circular" else n-1
    if parameters>4096 or parameters+reps*edges>10000:
        raise ResourceLimit("ansatz exceeds 4096 parameters or 10000 instructions")
    return Circuit._native_ansatz(n,rotations,entanglement,reps,prefix)


def maxcut_hamiltonian(n,edges,*,weights=None):
    """C = sum w_ij (I-Z_i Z_j)/2 in absolute native wire order."""
    from collections.abc import Mapping
    from itertools import islice
    from math import fsum
    from ._validation import _real,ResourceLimit
    from ._observable import Observable
    n=_int(n,2)
    if n>62:
        raise ResourceLimit("MaxCut observable limited to 62 wires")
    if isinstance(edges,(str,bytes,Mapping,set,frozenset)):
        raise ValueError("expected ordered edges")
    rows=[]
    seen=set()
    try:
        for raw in islice(iter(edges),256):
            if isinstance(raw,(str,bytes,Mapping,set,frozenset)):
                raise ValueError("expected ordered edge endpoints")
            pair=tuple(_int(w) for w in islice(iter(raw),3))
            if len(pair)!=2 or pair[0]==pair[1] or max(pair)>=n:
                raise ValueError("invalid edge")
            key=tuple(sorted(pair))
            if key in seen:
                raise ValueError("duplicate undirected edge")
            rows.append(key)
            seen.add(key)
    except TypeError as exc:
        raise ValueError("expected ordered edges") from exc
    if not 1<=len(rows)<=255:
        raise ResourceLimit("MaxCut requires 1..255 edges")
    if weights is None:
        values=(1.,)*len(rows)
    else:
        if isinstance(weights,(str,bytes,Mapping,set,frozenset)):
            raise ValueError("expected ordered edge weights")
        try:
            values=tuple(_real(v) for v in islice(iter(weights),len(rows)+1))
        except TypeError as exc:
            raise ValueError("expected ordered edge weights") from exc
        if len(values)!=len(rows):
            raise ValueError("one weight per edge required")
    terms={"I"*n:_real(fsum(v/2 for v in values))}
    for (a,b),value in zip(rows,values,strict=True):
        label=["I"]*n
        label[n-1-a]=label[n-1-b]="Z"
        terms["".join(label)]=-value/2
    return Observable(terms)


def phase_oracle(marked):
    """Apply -1 exactly to selected basis labels; no classical oracle synthesis."""
    from collections.abc import Mapping
    from itertools import islice
    from ._validation import ResourceLimit
    if isinstance(marked,str):
        labels=(marked,)
    else:
        if isinstance(marked,(bytes,Mapping,set,frozenset)):
            raise ValueError("expected one label or ordered labels")
        try:
            labels=tuple(islice(iter(marked),257))
        except TypeError as exc:
            raise ValueError("expected one label or ordered labels") from exc
    if not 1<=len(labels)<=256:
        raise ResourceLimit("phase oracle requires 1..256 labels")
    if any(type(label) is not str or not 2<=len(label)<=8 or set(label)-set("01") for label in labels):
        raise ValueError("expected basis labels with 2..8 bits")
    n=len(labels[0])
    if any(len(label)!=n for label in labels) or len(set(labels))!=len(labels):
        raise ValueError("expected distinct equal-width labels")
    c=Circuit(n)
    # Keep caller label order; cancel only adjacent X masks between marks.
    # Every marked phase is conjugated by its own mask and the final mask
    # is uncomputed. No assumption about the input state or clean ancillas.
    current=set()
    for label in labels:
        wanted={i for i,b in enumerate(reversed(label)) if b=="0"}
        change=sorted(current^wanted)
        if change:
            c.x(change)
        if n==2:
            c.cz(0,1)
        else:
            c.h(n-1).mcx(range(n-1),n-1).h(n-1)
        current=wanted
    if current:
        c.x(sorted(current))
    return c


def amplitude_amplification(oracle,*,iterations):
    """Uniform-input Grover iterate for an explicit bound phase-oracle promise.

    Caller promises a diagonal sign oracle. No promise verification or
    automatic iteration selection; the returned circuit does not execute.
    """
    from math import pi
    from ._validation import ResourceLimit
    if not isinstance(oracle,Circuit):
        raise TypeError("expected Circuit phase oracle")
    oracle._require_bound()
    n=oracle.num_qubits
    count=_int(iterations)
    if not 2<=n<=8 or count>64:
        raise ResourceLimit("amplification supports 2..8 wires and 0..64 iterations")
    # Bound total logical expansion before allocating or mutating a circuit.
    if count*(len(oracle._qc.data)+4*n+3)>100000:
        raise ResourceLimit("amplification exceeds 100000 estimated instructions")
    c=Circuit(n).h(range(n))
    if count==0:
        return c
    diffusion=Circuit(n).h(range(n)).apply(phase_oracle("0"*n)).h(range(n))
    diffusion._qc.global_phase += pi
    layer=Circuit(n).apply(oracle).apply(diffusion)
    return c.apply(layer,times=count)
