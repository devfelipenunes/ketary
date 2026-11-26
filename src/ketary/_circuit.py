"""Circuit facade and gate operations; Qiskit owns the circuit model."""
from __future__ import annotations
from ._adapter import _sdk, _validate, _validate_gate
from ._validation import _int, _limit, _angle, UnsupportedOperation
from ._result import Result
from ._trace import _Debug
from ._resources import _Resources, _Visualize
from ._checks import _CircuitChecks

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

    @property
    def test(self):
        return _CircuitChecks(self)

    @property
    def resources(self):
        return _Resources(self)

    @property
    def visualize(self):
        return _Visualize(self)

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

    def inspect(self, *, start=0, limit=32):
        """Research candidate: bounded logical operations, no copy or run."""
        from ._inspection import inspect_circuit
        return inspect_circuit(self,start=start,limit=limit)

    # Research-only syntax aliases. Existing gates namespace stays unchanged.
    def h(self,q):
        return self.gates.h(q)

    def x(self,q):
        return self.gates.x(q)

    def y(self,q):
        return self.gates.y(q)

    def z(self,q):
        return self.gates.z(q)

    def s(self,q):
        return self.gates.s(q)

    def sdg(self,q):
        return self.gates.sdg(q)

    def t(self,q):
        return self.gates.t(q)

    def tdg(self,q):
        return self.gates.tdg(q)

    def rx(self,theta,q):
        return self.gates.rx(theta,q)

    def ry(self,theta,q):
        return self.gates.ry(theta,q)

    def rz(self,theta,q):
        return self.gates.rz(theta,q)

    def cx(self,c,t):
        return self.gates.cx(c,t)

    def cz(self,c,t):
        return self.gates.cz(c,t)

    def swap(self,a,b):
        return self.gates.swap(a,b)

    def ccx(self,c1,c2,t):
        return self.gates.ccx(c1,c2,t)

    def p(self,theta,q):
        return self.gates.p(theta,q)

    def u(self,theta,phi,lam,q):
        return self.gates.u(theta,phi,lam,q)

    def cp(self,theta,a,b):
        return self.gates.cp(theta,a,b)

    def ch(self,a,b):
        return self.gates.ch(a,b)

    def crx(self,theta,a,b):
        return self.gates.crx(theta,a,b)

    def cry(self,theta,a,b):
        return self.gates.cry(theta,a,b)

    def crz(self,theta,a,b):
        return self.gates.crz(theta,a,b)

    def sx(self,q):
        return self.gates.sx(q)

    def sxdg(self,q):
        return self.gates.sxdg(q)

    def cy(self,a,b):
        return self.gates.cy(a,b)

    def cswap(self,control,a,b):
        return self.gates.cswap(control,a,b)

    def rxx(self,theta,a,b):
        return self.gates.rxx(theta,a,b)

    def ryy(self,theta,a,b):
        return self.gates.ryy(theta,a,b)

    def rzz(self,theta,a,b):
        return self.gates.rzz(theta,a,b)

    def copy(self):
        """Independent logical circuit with identical ordered operations."""
        return self._from_native(self._qc.copy(),owned=True)

    def h_many(self,wires):
        """Apply H on distinct wires after validating the entire batch."""
        from itertools import islice
        indices=[self.gates._wire(w) for w in islice(iter(wires),self.num_qubits+1)]
        if not indices or len(indices)>self.num_qubits or len(set(indices))!=len(indices):
            raise ValueError("expected nonempty distinct wires")
        for w in indices:
            self.h(w)
        return self

    def to_qiskit(self):
        return self._qc.copy()

    def compose(self,other,*,wires=None):
        if not isinstance(other,Circuit):
            raise TypeError("expected Circuit")
        indices=list(range(other.num_qubits)) if wires is None else [_int(i) for i in wires]
        if len(indices)!=other.num_qubits or len(set(indices))!=len(indices) or any(i>=self.num_qubits for i in indices):
            raise ValueError("invalid wire mapping")
        # Composition of two validated logical circuits is closed under the gate
        # whitelist. Native imports, append and non-closed transforms retain
        # their validation. Do not scan both gate lists again on this path.
        native=self._qc.compose(other._qc,qubits=indices,inplace=False)
        composed=Circuit.__new__(Circuit)
        composed._qc=native
        return composed

    def append(self, gate, wires):
        """Append a supported native gate after validating all inputs."""
        _validate_gate(gate)
        indices=[self.gates._wire(i) for i in wires]
        if len(indices)!=gate.num_qubits or len(set(indices))!=len(indices):
            raise ValueError("invalid gate wire mapping")
        self._qc.append(gate,indices,copy=True)
        return self

    def to_json(self):
        """Serialize the supported logical circuit to a bounded versioned artifact."""
        from ._replay import _encode
        return _encode(self)

    @classmethod
    def from_json(cls,payload):
        """Reconstruct a supported logical circuit without executing it."""
        from ._replay import _decode
        return cls._from_native(_decode(payload),owned=True)

    def transpile(self, *, basis_gates, seed=42):
        """Experimental logical-only Qiskit lowering, verified by full operators.

        No backend, target, coupling map or layout is accepted. Limited to
        eight qubits because strict phase-preserving equivalence is checked.
        """
        from ._transpilation import _lower
        return _lower(self,basis_gates=basis_gates,seed=seed)

    def optimize(self):
        """Return a new circuit after conservative adjacent inverse cancellation."""
        from ._optimization import _cancel_adjacent
        return self._from_native(_cancel_adjacent(self._qc),owned=True)

    def inverse(self):
        return self._from_native(self._qc.inverse(),owned=True)

    def decompose(self,*,reps=1):
        # Selective SWAP lowering: general decomposition leaves the whitelist.
        return self._from_native(self._qc.decompose(gates_to_decompose=["swap"], reps=_int(reps,1)),owned=True)

    def run(self,*,mode="statevector",max_bytes=64*1024**2,initial_state=None):
        if mode!="statevector":
            raise UnsupportedOperation("only ideal statevector in PoC")
        _limit(self.num_qubits,budget=max_bytes)
        _,SV=_sdk()
        if initial_state is None:
            return Result(SV.from_instruction(self._qc).data)
        if isinstance(initial_state,str):
            if len(initial_state)!=self.num_qubits or set(initial_state)-{"0","1"}:
                raise ValueError("invalid initial basis label")
            state=SV.from_label(initial_state)
        else:
            snapshot=initial_state if isinstance(initial_state,Result) else Result(initial_state)
            if snapshot.num_qubits!=self.num_qubits:
                raise ValueError("initial state width mismatch")
            state=SV(snapshot.math.statevector(max_bytes=max_bytes))
        return Result(state.evolve(self._qc).data)

class _Gates:
    def __init__(self,c):
        self._c=c

    def _wire(self,q):
        # Builtin ints are the common case; keep full validation for other
        # integer-like values and reject bools, floats and negative indices.
        if type(q) is not int:
            q=_int(q)
        if q<0 or q>=self._c.num_qubits:
            raise ValueError("invalid wire")
        return q

    def _pair(self,a,b):
        a=self._wire(a)
        b=self._wire(b)
        if a==b:
            raise ValueError("duplicate wires")
        return a,b

    def h(self,q):
        self._c._qc.h(self._wire(q))
        return self._c

    def x(self,q):
        self._c._qc.x(self._wire(q))
        return self._c

    def z(self,q):
        self._c._qc.z(self._wire(q))
        return self._c

    def cx(self,c,t):
        c,t=self._pair(c,t)
        self._c._qc.cx(c,t)
        return self._c

    def swap(self,a,b):
        a,b=self._pair(a,b)
        self._c._qc.swap(a,b)
        return self._c

    def y(self,q):
        self._c._qc.y(self._wire(q))
        return self._c

    def s(self,q):
        self._c._qc.s(self._wire(q))
        return self._c

    def t(self,q):
        self._c._qc.t(self._wire(q))
        return self._c

    def sdg(self,q):
        self._c._qc.sdg(self._wire(q))
        return self._c

    def tdg(self,q):
        self._c._qc.tdg(self._wire(q))
        return self._c

    def rx(self,theta,q):
        self._c._qc.rx(_angle(theta),self._wire(q))
        return self._c

    def ry(self,theta,q):
        self._c._qc.ry(_angle(theta),self._wire(q))
        return self._c

    def rz(self,theta,q):
        self._c._qc.rz(_angle(theta),self._wire(q))
        return self._c

    def cz(self,c,t):
        c,t=self._pair(c,t)
        self._c._qc.cz(c,t)
        return self._c

    def ccx(self,c1,c2,t):
        c1,c2,t=(self._wire(i) for i in (c1,c2,t))
        if len({c1,c2,t})!=3:
            raise ValueError("duplicate wires")
        self._c._qc.ccx(c1,c2,t)
        return self._c

    def p(self,theta,q):
        from qiskit.circuit.library import PhaseGate
        return self._c.append(PhaseGate(_angle(theta)),[q])

    def u(self,theta,phi,lam,q):
        from qiskit.circuit.library import UGate
        return self._c.append(UGate(_angle(theta),_angle(phi),_angle(lam)),[q])

    def cp(self,theta,a,b):
        from qiskit.circuit.library import CPhaseGate
        return self._c.append(CPhaseGate(_angle(theta)),[a,b])

    def ch(self,a,b):
        from qiskit.circuit.library import CHGate
        return self._c.append(CHGate(),[a,b])

    def crx(self,theta,a,b):
        from qiskit.circuit.library import CRXGate
        return self._c.append(CRXGate(_angle(theta)),[a,b])

    def cry(self,theta,a,b):
        from qiskit.circuit.library import CRYGate
        return self._c.append(CRYGate(_angle(theta)),[a,b])

    def crz(self,theta,a,b):
        from qiskit.circuit.library import CRZGate
        return self._c.append(CRZGate(_angle(theta)),[a,b])

    def sx(self,q):
        from qiskit.circuit.library import SXGate
        return self._c.append(SXGate(),[q])

    def sxdg(self,q):
        from qiskit.circuit.library import SXdgGate
        return self._c.append(SXdgGate(),[q])

    def cy(self,a,b):
        from qiskit.circuit.library import CYGate
        return self._c.append(CYGate(),[a,b])

    def cswap(self,control,a,b):
        from qiskit.circuit.library import CSwapGate
        return self._c.append(CSwapGate(),[control,a,b])

    def rxx(self,theta,a,b):
        from qiskit.circuit.library import RXXGate
        return self._c.append(RXXGate(_angle(theta)),[a,b])

    def ryy(self,theta,a,b):
        from qiskit.circuit.library import RYYGate
        return self._c.append(RYYGate(_angle(theta)),[a,b])

    def rzz(self,theta,a,b):
        from qiskit.circuit.library import RZZGate
        return self._c.append(RZZGate(_angle(theta)),[a,b])

def from_qiskit(qc):
    return Circuit._from_native(qc)
