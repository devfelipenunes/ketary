"""Circuit facade and gate operations; Qiskit owns the circuit model."""
from __future__ import annotations
from ._adapter import _sdk, _validate, _validate_gate, _gate_angle
from ._validation import _int, _limit, _angle, UnsupportedOperation
from ._trace import _Debug
from ._resources import _Resources, _Visualize
from ._checks import _CircuitChecks

class Circuit:
    """One builder, one authoritative Qiskit circuit (strict PoC subset)."""

    def __init__(self,n):
        QC,_=_sdk()
        self._qc=QC(_int(n,1))

    @classmethod
    def classical(cls,n,num_clbits):
        """Explicit local dynamic-circuit builder with one classical register."""
        from ._validation import ResourceLimit
        n,bits=_int(n,1),_int(num_clbits,1)
        if n>12 or bits>12:
            raise ResourceLimit("classical builder limited to 12 wires and bits")
        QC,_=_sdk()
        c=cls(n)
        c._qc=QC(n,bits)
        return c

    @property
    def capabilities(self):
        """Runtime capability report, not a second circuit model."""
        classical=bool(self.num_clbits)
        unbound=bool(self._qc.parameters)
        return {"mode":"classical" if classical else "symbolic" if getattr(self,"_symbolic",False) else "unitary",
                "run_statevector":not classical and not unbound,
                "run_shots":classical and not unbound,
                "bound_transforms":not classical and not unbound,
                "bind":not classical,"logical_replay":not classical and not unbound}

    @property
    def num_clbits(self):
        return self._qc.num_clbits

    def _classical_bit(self,bit):
        bit=_int(bit)
        if not self.num_clbits:
            raise UnsupportedOperation("use Circuit.classical for measurement/control")
        if bit>=self.num_clbits:
            raise ValueError("invalid classical bit")
        return bit

    def measure(self,wire,bit):
        """Measure scalar wire/bit or aligned distinct ordered sequences."""
        if hasattr(wire,"__index__"):
            wire=self.gates._wire(wire)
            bit=self._classical_bit(bit)
            self._qc.measure(wire,bit)
            return self
        from ._ergonomics import _selection
        from collections.abc import Mapping
        from itertools import islice
        if not self.num_clbits:
            raise UnsupportedOperation("use Circuit.classical for measurement/control")
        wires=_selection(self,wire)
        if isinstance(bit,(str,bytes,Mapping,set,frozenset)):
            raise ValueError("expected an ordered iterable of classical bits")
        try:
            bits=tuple(self._classical_bit(b) for b in islice(iter(bit),len(wires)+1))
        except TypeError as exc:
            raise ValueError("expected an ordered iterable of classical bits") from exc
        if len(bits)!=len(wires) or len(set(bits))!=len(bits):
            raise ValueError("expected equal-length wire and distinct bit sequences")
        candidate=self._qc.copy()
        for w,b in zip(wires,bits):
            candidate.measure(w,b)
        self._qc=candidate
        return self

    def reset(self,wire):
        """Reset one wire or an ordered selection of distinct wires."""
        if not self.num_clbits:
            raise UnsupportedOperation("use Circuit.classical for reset")
        if hasattr(wire,"__index__"):
            self._qc.reset(self.gates._wire(wire))
            return self
        from ._ergonomics import _selection
        wires=_selection(self,wire)
        candidate=self._qc.copy()
        for w in wires:
            candidate.reset(w)
        self._qc=candidate
        return self

    def _conditional(self,gate,wire,bit,value):
        wire=self.gates._wire(wire)
        bit=self._classical_bit(bit)
        value=_int(value)
        if value not in (0,1):
            raise ValueError("condition must be zero or one")
        with self._qc.if_test((self._qc.clbits[bit],value)):
            getattr(self._qc,gate)(wire)
        return self

    def if_x(self,wire,bit,*,value=1):
        return self._conditional("x",wire,bit,value)

    def if_z(self,wire,bit,*,value=1):
        return self._conditional("z",wire,bit,value)

    def run_shots(self,*,shots=1024,seed=None,max_bytes=64*1024**2):
        """Explicit local execution using the optional Qiskit Aer extra."""
        from ._classical import run_shots
        return run_shots(self,shots=shots,seed=seed,max_bytes=max_bytes)

    @classmethod
    def from_dynamic(cls,template):
        """Import an independent bounded native dynamic circuit."""
        from ._classical import _dynamic_snapshot
        c=cls.__new__(cls)
        c._qc=_dynamic_snapshot(template)
        return c

    def run_density(self,initial_state=None,*,max_bytes=64*1024**2):
        """Explicit ideal density-matrix evolution; returns native DensityMatrix."""
        from ._classical import _run_density
        return _run_density(self,initial_state,max_bytes=max_bytes)

    def run_noisy(self,noise_model,*,seed=None,max_bytes=64*1024**2):
        """Explicit optional Aer density-matrix noise simulation."""
        from ._classical import _run_noisy
        return _run_noisy(self,noise_model,seed=seed,max_bytes=max_bytes)

    def transpile_for(self,backend,*,optimization_level=0,seed=0):
        """Return an explicitly target-transpiled native circuit, never submit a job."""
        from ._transpilation import _transpile_for
        return _transpile_for(self,backend,optimization_level=optimization_level,seed=seed)

    @classmethod
    def symbolic(cls,n):
        """Explicit opt-in to native symbolic gate parameters."""
        c=cls(n)
        c._symbolic=True
        return c

    @staticmethod
    def parameter(name):
        if type(name) is not str or not name or len(name)>128:
            raise ValueError("expected a nonempty parameter name up to 128 characters")
        from qiskit.circuit import Parameter
        return Parameter(name)

    @staticmethod
    def parameter_vector(name,size):
        """Independent native parameter identities in declared vector order."""
        from qiskit.circuit import ParameterVector
        from ._validation import ResourceLimit
        if type(name) is not str or not name or len(name)>112:
            raise ValueError("expected a nonempty parameter prefix up to 112 characters")
        size=_int(size,1)
        if size>4096:
            raise ResourceLimit("parameter vector limited to 4096 elements")
        return tuple(ParameterVector(name,size))

    @classmethod
    def _native_ansatz(cls,n,rotations,entanglement,reps,prefix):
        from qiskit.circuit.library import n_local
        native=n_local(n,rotation_blocks=list(rotations),entanglement_blocks="cx",
                       entanglement=entanglement,reps=reps,parameter_prefix=prefix)
        _validate(native,allow_parameters=True)
        c=cls.__new__(cls)
        c._qc=native
        c._symbolic=True
        return c

    @property
    def parameters(self):
        return tuple(self._qc.parameters)

    def bind(self,bindings=None,**values):
        """Return an independent fully bound circuit; source is unchanged."""
        if self.num_clbits:
            raise UnsupportedOperation('symbolic classical binding is outside this subset')
        if bindings is not None and values:
            raise ValueError("choose a parameter mapping or named values")
        if bindings is None:
            params={p.name:p for p in self.parameters}
            if len(params)!=len(self.parameters) or set(values)!=set(params):
                raise ValueError("named binding must cover each unique parameter")
            bindings={params[name]:value for name,value in values.items()}
        else:
            from collections.abc import Mapping
            from itertools import islice
            if not isinstance(bindings,Mapping):
                if isinstance(bindings,(str,bytes,set,frozenset)):
                    raise TypeError("expected mapping or ordered numeric values")
                params=self.parameters
                try:
                    vals=tuple(islice(iter(bindings),len(params)+1))
                except TypeError as exc:
                    raise TypeError("expected mapping or ordered numeric values") from exc
                if len(vals)!=len(params):
                    raise ValueError("ordered binding must cover exactly the native parameter order")
                bindings=dict(zip(params,vals,strict=True))
        # Only internal circuits have the validated structure invariant.
        # Native assignment preserves it; check evaluated numeric values,
        # including expression overflow, without rechecking every gate kind.
        from ._adapter import _validate_bound_values
        from ._validation import _angle
        if set(bindings)!=set(self._qc.parameters):
            raise ValueError("bindings must cover exactly the template parameters")
        numeric={key:_angle(value) for key,value in bindings.items()}
        try:
            bound=self._qc.assign_parameters(numeric,inplace=False,flat_input=True)
        except (ZeroDivisionError,OverflowError) as exc:
            raise ValueError("parameter expression must evaluate to a finite real number") from exc
        _validate_bound_values(bound)
        c=Circuit.__new__(Circuit)
        c._qc=bound
        return c

    def _bind_numeric(self,numeric):
        """Sweep-only assignment for complete, preflighted finite rows.

        Keep the scalar public binding body unchanged: paired measurements
        showed a regression with an extra shared dispatch. Both paths keep
        native assignment, exception translation and bound-value validation.
        """
        from ._adapter import _validate_bound_values
        try:
            bound=self._qc.assign_parameters(numeric,inplace=False,flat_input=True)
        except (ZeroDivisionError,OverflowError) as exc:
            raise ValueError("parameter expression must evaluate to a finite real number") from exc
        _validate_bound_values(bound)
        c=Circuit.__new__(Circuit)
        c._qc=bound
        return c

    def expectation_jacobian(self,bindings,observables,*,max_bytes=64*1024**2):
        """Explicit ideal expectation derivatives in observable/native parameter order."""
        from ._ergonomics import _expectation_jacobian
        return _expectation_jacobian(self,bindings,observables,max_bytes=max_bytes)

    def sweep(self,**values):
        """Construct a bounded zipped parameter plan without execution."""
        from ._ergonomics import SweepPlan
        return SweepPlan(self,values)

    def sweep_rows(self,rows):
        """Freeze complete numeric parameter rows in native order."""
        from ._ergonomics import _sweep_rows
        return _sweep_rows(self,rows)

    def register(self,name,wires):
        """Name a logical selection; no allocation or native register mutation."""
        from ._ergonomics import _selection,_name
        name=_name(name)
        selected=_selection(self,wires)
        names=getattr(self,"_named_registers",{})
        if name in names:
            raise ValueError("duplicate register name")
        if len(names)>=32:
            from ._validation import ResourceLimit
            raise ResourceLimit("at most 32 named selections")
        self._named_registers={**names,name:selected}
        return selected

    @property
    def registers(self):
        return dict(getattr(self,"_named_registers",{}))

    def checkpoint(self,name):
        """Record an append-only prefix index, not an operation or measurement."""
        from ._ergonomics import _name
        self._require_bound()
        name=_name(name)
        points=getattr(self,"_named_checkpoints",{})
        if name in points:
            raise ValueError("duplicate checkpoint name")
        if len(points)>=32:
            from ._validation import ResourceLimit
            raise ResourceLimit("at most 32 named checkpoints")
        self._named_checkpoints={**points,name:len(self._qc.data)}
        return self

    @property
    def checkpoints(self):
        return dict(getattr(self,"_named_checkpoints",{}))

    def _checkpoint_index(self,index):
        if isinstance(index,str):
            points=self.checkpoints
            if index not in points:
                raise ValueError("unknown checkpoint name")
            return points[index]
        return _int(index)

    def contract(self,*,probabilities=None,expectations=None,normalized=False,atol=1e-9):
        from ._contracts import Contract
        return Contract(self.num_qubits,probabilities=probabilities,expectations=expectations,normalized=normalized,atol=atol)

    def apply(self,block,*,wires=None,times=1):
        """Append a block sequentially; unbound blocks require a symbolic target."""
        count=_int(times,1)
        self._require_application(block)
        indices=self._mapping_wires(block,wires)
        if count!=1:
            self._check_expansion(block,count)
        return self._apply_placements(block,(indices for _ in range(count)))

    def apply_each(self,block,*,placements):
        """Apply one block to each ordered placement, sequentially."""
        from collections.abc import Mapping
        from itertools import islice
        from ._validation import ResourceLimit
        self._require_application(block)
        if isinstance(placements,(str,bytes,set,frozenset,Mapping)):
            raise ValueError("placements must be an ordered iterable")
        try:
            iterator=iter(placements)
        except TypeError as exc:
            raise ValueError("placements must be an ordered iterable") from exc
        rows=[]
        for wires in islice(iterator,10001):
            self._check_expansion(block,len(rows)+1)
            if wires is None:
                raise ValueError("each placement must explicitly select wires")
            rows.append(self._mapping_wires(block,wires))
        if not rows:
            raise ValueError("expected at least one placement")
        return self._apply_placements(block,rows)

    @staticmethod
    def _check_expansion(block,count):
        from ._validation import ResourceLimit
        if count>10000 or len(block._qc.data)*count>100000:
            raise ResourceLimit("expansion supports <=10000 placements and 100000 appended operations")


    def _require_application(self,block):
        if not isinstance(block,Circuit):
            raise TypeError("expected Circuit")
        if not getattr(self,"_symbolic",False):
            self._require_bound()
            block._require_bound()
            return
        if self.num_clbits or block.num_clbits:
            raise UnsupportedOperation("symbolic composition requires unitary circuits")
        # Same native parameter may be shared, but a distinct UUID with the
        # same name is ambiguous. Never silently rename or bind a parameter.
        existing={p.name:p for p in self.parameters}
        for p in block.parameters:
            if p.name in existing and existing[p.name]!=p:
                raise ValueError("conflicting parameter name; reuse the same native Parameter")

    def _apply_placements(self,block,placements):
        from ._adapter import _append_bound_blocks
        # Both bound and symbolic unitary sources are preflighted, including
        # parameter identity and wire mappings. Self-application snapshots
        # its source once; ordinary composition rolls back suffix and phase.
        changed=_append_bound_blocks(self._qc,block._qc,placements)
        if changed:
            self._named_checkpoints={}
        return self

    def repeat(self,times):
        """Return an independent repeated circuit; unbound mode stays symbolic."""
        count=_int(times,1)
        if self._qc.parameters and getattr(self,"_symbolic",False):
            target=Circuit.symbolic(self.num_qubits)
        else:
            self._require_bound()
            target=Circuit(self.num_qubits)
        self._check_expansion(self,count)
        return target.apply(self,times=count)

    def evolve(self,observable,*,time):
        """Append exp(-i*time*H) for a commuting real Pauli Observable."""
        from ._ergonomics import _evolve
        return _evolve(self,observable,time)

    def compute_action_uncompute(self,compute,action,*,compute_wires,action_wires):
        """Explicit U, V, U^-1 sequence; no claim that ancillas are cleared."""
        # Materialize once, validate both mappings before committing.
        from ._ergonomics import _selection
        cw=_selection(self,compute_wires)
        aw=_selection(self,action_wires)
        candidate=self.compose(compute,wires=cw).compose(action,wires=aw).compose(compute.inverse(),wires=cw)
        if candidate._qc.global_phase!=self._qc.global_phase:
            self._named_checkpoints={}
        self._qc=candidate._qc
        return self

    def _require_bound(self):
        if self.num_clbits:
            raise UnsupportedOperation('classical circuit requires run_shots; unitary operations are unavailable')
        if self._qc.parameters:
            raise UnsupportedOperation("bind all symbolic parameters before this operation")

    def _gate_angle(self,value):
        return _gate_angle(value,allow_parameters=getattr(self,"_symbolic",False))

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

    @property
    def wires(self):
        """Logical indices in ascending order; no native allocation."""
        return range(self.num_qubits)

    @classmethod
    def _from_native(cls,qc,*,owned=False):
        _validate(qc)
        c=cls.__new__(cls)
        c._qc=qc if owned else qc.copy()
        return c

    @classmethod
    def from_parameterized(cls, template, bindings):
        """Bind all parameters in a trusted native template before import.

        Unbound circuits never enter the Ketary logical Circuit.
        """
        from collections.abc import Mapping
        QC,_=_sdk()
        if not isinstance(template,QC) or not isinstance(bindings,Mapping):
            raise TypeError("expected QuantumCircuit and parameter mapping")
        if set(bindings)!=set(template.parameters):
            raise ValueError("bindings must cover exactly the template parameters")
        bound=template.assign_parameters({key:_angle(value) for key,value in bindings.items()},inplace=False)
        return cls._from_native(bound,owned=True)

    def plan(self,*,bits=(),paulis=(),subsystems=()):
        from ._plan import QueryPlan
        return QueryPlan(self,bits=bits,paulis=paulis,subsystems=subsystems)

    def diff(self,other,*,atol=1e-9,max_bytes=64*1024**2):
        """Explicit structural, snapshot and operator comparison."""
        from ._verification import semantic_diff
        from ._reports import SemanticDiffReport
        return SemanticDiffReport(semantic_diff(self,other,atol=atol,max_bytes=max_bytes))

    def inspect(self, *, start=0, limit=32):
        """Bounded logical operations, no copy or execution."""
        self._require_bound()
        from ._inspection import inspect_circuit
        return inspect_circuit(self,start=start,limit=limit)

    # Fluent aliases; the existing gates namespace remains compatible.
    def h(self,q):
        from ._ergonomics import _single
        return _single(self,"h",q)

    def x(self,q):
        from ._ergonomics import _single
        return _single(self,"x",q)

    def y(self,q):
        from ._ergonomics import _single
        return _single(self,"y",q)

    def z(self,q):
        from ._ergonomics import _single
        return _single(self,"z",q)

    def s(self,q):
        from ._ergonomics import _single
        return _single(self,"s",q)

    def sdg(self,q):
        from ._ergonomics import _single
        return _single(self,"sdg",q)

    def t(self,q):
        from ._ergonomics import _single
        return _single(self,"t",q)

    def tdg(self,q):
        from ._ergonomics import _single
        return _single(self,"tdg",q)

    def rx(self,theta,q):
        from ._ergonomics import _rotation
        return _rotation(self,"rx",theta,q)

    def ry(self,theta,q):
        from ._ergonomics import _rotation
        return _rotation(self,"ry",theta,q)

    def rz(self,theta,q):
        from ._ergonomics import _rotation
        return _rotation(self,"rz",theta,q)

    def cx(self,c=None,t=None,*,pairs=None):
        if pairs is None:
            return self.gates.cx(c,t)
        from ._ergonomics import _pairs
        return _pairs(self,"cx",c,t,pairs)

    def cz(self,c=None,t=None,*,pairs=None):
        if pairs is None:
            return self.gates.cz(c,t)
        from ._ergonomics import _pairs
        return _pairs(self,"cz",c,t,pairs)

    def swap(self,a=None,b=None,*,pairs=None):
        if pairs is None:
            return self.gates.swap(a,b)
        from ._ergonomics import _pairs
        return _pairs(self,"swap",a,b,pairs)

    def ccx(self,c1,c2,t):
        return self.gates.ccx(c1,c2,t)

    def p(self,theta,q):
        from ._ergonomics import _rotation
        return _rotation(self,"p",theta,q)

    def u(self,theta,phi,lam,q):
        from ._ergonomics import _single
        return _single(self,"u",q,theta,phi,lam)

    def cp(self,theta,a=None,b=None,*,pairs=None):
        if pairs is None:
            return self.gates.cp(theta,a,b)
        from ._ergonomics import _pairs
        return _pairs(self,"cp",a,b,pairs,theta)

    def ch(self,a=None,b=None,*,pairs=None):
        if pairs is None:
            return self.gates.ch(a,b)
        from ._ergonomics import _pairs
        return _pairs(self,"ch",a,b,pairs)

    def crx(self,theta,a=None,b=None,*,pairs=None):
        if pairs is None:
            return self.gates.crx(theta,a,b)
        from ._ergonomics import _pairs
        return _pairs(self,"crx",a,b,pairs,theta)

    def cry(self,theta,a=None,b=None,*,pairs=None):
        if pairs is None:
            return self.gates.cry(theta,a,b)
        from ._ergonomics import _pairs
        return _pairs(self,"cry",a,b,pairs,theta)

    def crz(self,theta,a=None,b=None,*,pairs=None):
        if pairs is None:
            return self.gates.crz(theta,a,b)
        from ._ergonomics import _pairs
        return _pairs(self,"crz",a,b,pairs,theta)

    def sx(self,q):
        from ._ergonomics import _single
        return _single(self,"sx",q)

    def sxdg(self,q):
        from ._ergonomics import _single
        return _single(self,"sxdg",q)

    def cy(self,a=None,b=None,*,pairs=None):
        if pairs is None:
            return self.gates.cy(a,b)
        from ._ergonomics import _pairs
        return _pairs(self,"cy",a,b,pairs)

    def cswap(self,control,a,b):
        return self.gates.cswap(control,a,b)

    def rxx(self,theta,a=None,b=None,*,pairs=None):
        if pairs is None:
            return self.gates.rxx(theta,a,b)
        from ._ergonomics import _pairs
        return _pairs(self,"rxx",a,b,pairs,theta)

    def ryy(self,theta,a=None,b=None,*,pairs=None):
        if pairs is None:
            return self.gates.ryy(theta,a,b)
        from ._ergonomics import _pairs
        return _pairs(self,"ryy",a,b,pairs,theta)

    def rzz(self,theta,a=None,b=None,*,pairs=None):
        if pairs is None:
            return self.gates.rzz(theta,a,b)
        from ._ergonomics import _pairs
        return _pairs(self,"rzz",a,b,pairs,theta)

    def mcx(self,controls,target):
        return self.gates.mcx(controls,target)

    def copy(self):
        """Independent logical circuit with identical ordered operations."""
        if self.num_clbits:
            c=self.classical(self.num_qubits,self.num_clbits)
            c._qc=self._qc.copy()
            return self._copy_annotations(c)
        if getattr(self,"_symbolic",False):
            c=self.symbolic(self.num_qubits)
            c._qc=self._qc.copy()
            return self._copy_annotations(c)
        return self._copy_annotations(self._from_native(self._qc.copy(),owned=True))

    def _copy_annotations(self,c):
        c._named_registers=self.registers
        c._named_checkpoints=self.checkpoints
        return c

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

    def _composition_wires(self,other,wires):
        if not isinstance(other,Circuit):
            raise TypeError("expected Circuit")
        self._require_bound()
        other._require_bound()
        return self._mapping_wires(other,wires)

    def _mapping_wires(self,other,wires):
        from itertools import islice
        from collections.abc import Mapping
        if isinstance(wires,(str,bytes,set,frozenset,Mapping)):
            raise ValueError("wire mapping must be ordered")
        indices=list(range(other.num_qubits)) if wires is None else [_int(i) for i in islice(iter(wires),other.num_qubits+1)]
        if len(indices)!=other.num_qubits or len(set(indices))!=len(indices) or any(i>=self.num_qubits for i in indices):
            raise ValueError("invalid wire mapping")
        return indices

    def compose(self,other,*,wires=None):
        indices=self._composition_wires(other,wires)
        # Composition of two validated logical circuits is closed under the gate
        # whitelist. Native imports, append and non-closed transforms retain
        # their validation. Do not scan both gate lists again on this path.
        native=self._qc.compose(other._qc,qubits=indices,inplace=False)
        composed=Circuit.__new__(Circuit)
        composed._qc=native
        return composed

    def append(self, gate, wires):
        """Append a supported native gate after validating all inputs."""
        _validate_gate(gate,allow_parameters=getattr(self,'_symbolic',False))
        from itertools import islice
        from collections.abc import Mapping
        if isinstance(wires,(str,bytes,set,frozenset,Mapping)):
            raise ValueError("gate wire mapping must be ordered")
        indices=[self.gates._wire(i) for i in islice(iter(wires),gate.num_qubits+1)]
        if len(indices)!=gate.num_qubits or len(set(indices))!=len(indices):
            raise ValueError("invalid gate wire mapping")
        self._qc.append(gate,indices,copy=True)
        return self

    def to_json(self):
        """Serialize the supported logical circuit to a bounded versioned artifact."""
        self._require_bound()
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
        self._require_bound()
        from ._transpilation import _lower
        return _lower(self,basis_gates=basis_gates,seed=seed)

    def optimize(self):
        """Return a new circuit after conservative adjacent inverse cancellation."""
        self._require_bound()
        from ._optimization import _cancel_adjacent
        return self._from_native(_cancel_adjacent(self._qc),owned=True)

    def inverse(self):
        self._require_bound()
        return self._from_native(self._qc.inverse(),owned=True)

    def decompose(self,*,reps=1):
        # Selective SWAP lowering: general decomposition leaves the whitelist.
        self._require_bound()
        return self._from_native(self._qc.decompose(gates_to_decompose=["swap"], reps=_int(reps,1)),owned=True)

    def run(self,*,mode="statevector",max_bytes=64*1024**2,initial_state=None):
        self._require_bound()
        if mode!="statevector":
            raise UnsupportedOperation("only ideal statevector in PoC")
        _limit(self.num_qubits,budget=max_bytes)
        from ._execution import execute_ideal
        return execute_ideal(self._qc,initial_state,max_bytes)

    def run_many(self,initial_states,*,max_bytes=64*1024**2):
        """Independent ideal evolutions, in caller order; preflight all inputs."""
        from collections.abc import Mapping
        from itertools import islice
        from ._validation import ResourceLimit
        from ._execution import prepare_initial,execute_ideal
        self._require_bound()
        if isinstance(initial_states,(str,bytes,set,frozenset,Mapping)):
            raise ValueError("expected ordered initial states")
        try:
            states=tuple(islice(iter(initial_states),33))
        except TypeError as exc:
            raise ValueError("expected ordered initial states") from exc
        if not 1<=len(states)<=32:
            raise ResourceLimit("run_many requires 1..32 inputs")
        # Conservative payload: input snapshots + retained results + working
        # state. Not a process RSS guarantee. Validate before input copying.
        _limit(self.num_qubits,2*len(states)+1,budget=max_bytes)
        prepared=tuple(prepare_initial(self.num_qubits,state) for state in states)
        return tuple(execute_ideal(self._qc,state,max_bytes) for state in prepared)


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
        self._c._qc.rx(self._c._gate_angle(theta),self._wire(q))
        return self._c

    def ry(self,theta,q):
        self._c._qc.ry(self._c._gate_angle(theta),self._wire(q))
        return self._c

    def rz(self,theta,q):
        self._c._qc.rz(self._c._gate_angle(theta),self._wire(q))
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
        return self._c.append(PhaseGate(self._c._gate_angle(theta)),[q])

    def u(self,theta,phi,lam,q):
        from qiskit.circuit.library import UGate
        return self._c.append(UGate(self._c._gate_angle(theta),self._c._gate_angle(phi),self._c._gate_angle(lam)),[q])

    def cp(self,theta,a,b):
        from qiskit.circuit.library import CPhaseGate
        return self._c.append(CPhaseGate(self._c._gate_angle(theta)),[a,b])

    def ch(self,a,b):
        from qiskit.circuit.library import CHGate
        return self._c.append(CHGate(),[a,b])

    def crx(self,theta,a,b):
        from qiskit.circuit.library import CRXGate
        return self._c.append(CRXGate(self._c._gate_angle(theta)),[a,b])

    def cry(self,theta,a,b):
        from qiskit.circuit.library import CRYGate
        return self._c.append(CRYGate(self._c._gate_angle(theta)),[a,b])

    def crz(self,theta,a,b):
        from qiskit.circuit.library import CRZGate
        return self._c.append(CRZGate(self._c._gate_angle(theta)),[a,b])

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
        return self._c.append(RXXGate(self._c._gate_angle(theta)),[a,b])

    def ryy(self,theta,a,b):
        from qiskit.circuit.library import RYYGate
        return self._c.append(RYYGate(self._c._gate_angle(theta)),[a,b])

    def rzz(self,theta,a,b):
        from qiskit.circuit.library import RZZGate
        return self._c.append(RZZGate(self._c._gate_angle(theta)),[a,b])

    def mcx(self,controls,target):
        """Bounded closed controls, with CX/CCX canonical for one/two controls."""
        from itertools import islice
        from qiskit.circuit.library import MCXGate
        controls=tuple(self._wire(w) for w in islice(iter(controls),8))
        target=self._wire(target)
        if not 1<=len(controls)<=7 or len(set((*controls,target)))!=len(controls)+1:
            raise ValueError("expected 1..7 distinct controls and target")
        if len(controls)==1:
            return self.cx(controls[0],target)
        if len(controls)==2:
            return self.ccx(*controls,target)
        return self._c.append(MCXGate(len(controls)),[*controls,target])

def from_qiskit(qc):
    return Circuit._from_native(qc)
