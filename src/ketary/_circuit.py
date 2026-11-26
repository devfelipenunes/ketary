"""Circuit facade and gate operations; Qiskit owns the circuit model."""
from __future__ import annotations
from ._adapter import _sdk, _validate, _validate_gate
from ._validation import _int, _limit, _angle, UnsupportedOperation
from ._result import Result
from ._trace import _Debug
from ._resources import _Resources, _Visualize

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

    def to_qiskit(self):
        return self._qc.copy()

    def compose(self,other,*,wires=None):
        if not isinstance(other,Circuit):
            raise TypeError("expected Circuit")
        indices=list(range(other.num_qubits)) if wires is None else [_int(i) for i in wires]
        if len(indices)!=other.num_qubits or len(set(indices))!=len(indices) or any(i>=self.num_qubits for i in indices):
            raise ValueError("invalid wire mapping")
        return self._from_native(self._qc.compose(other._qc,qubits=indices,inplace=False),owned=True)

    def append(self, gate, wires):
        """Append a supported native gate after validating all inputs."""
        _validate_gate(gate)
        indices=[self.gates._wire(i) for i in wires]
        if len(indices)!=gate.num_qubits or len(set(indices))!=len(indices):
            raise ValueError("invalid gate wire mapping")
        self._qc.append(gate,indices,copy=True)
        return self

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

def from_qiskit(qc):
    return Circuit._from_native(qc)
