"""Bounded native local shot execution, separate from pure Result snapshots."""
from dataclasses import dataclass
from collections.abc import Mapping
from ._validation import _int,_limit,ResourceLimit,UnsupportedOperation

@dataclass(frozen=True)
class ShotResult:
    shots: int
    num_clbits: int
    seed: int | None
    _counts: tuple[tuple[str,int], ...]

    measurements: tuple[tuple[int,int,int], ...] = ()
    backend: str = "unknown"
    backend_version: str = "unknown"

    @property
    def measured_bits(self):
        return tuple(sorted({bit for _,_,bit in self.measurements}))

    @property
    def counts(self):
        return dict(self._counts)

    def probabilities(self):
        """Empirical frequencies, not exact Born probabilities."""
        return {label:count/self.shots for label,count in self._counts}


def run_shots(circuit,*,shots,seed,max_bytes):
    qc=circuit._qc
    if not qc.num_clbits or qc.parameters:
        raise UnsupportedOperation("shot execution requires a bound classical circuit")
    shots=_int(shots,1)
    if shots>10000 or qc.num_qubits>12 or qc.num_clbits>12 or len(qc.data)>1024:
        raise ResourceLimit("dynamic execution: <=12 wires/bits, 1024 instructions, 10000 shots")
    _limit(qc.num_qubits,budget=max_bytes)
    _validate_dynamic(qc)
    if seed is not None:
        seed=_int(seed)
        if seed>2**32-1:
            raise ValueError("seed exceeds unsigned 32-bit range")
    if not any(item.operation.name=="measure" for item in qc.data):
        raise ValueError("classical circuit requires a measurement")
    try:
        from qiskit_aer import AerSimulator
    except ImportError as exc:
        raise UnsupportedOperation("install ketary[dynamic] for local shot execution") from exc
    from qiskit import transpile
    backend=AerSimulator(method="statevector",max_parallel_threads=1)
    compiled=transpile(qc,backend=backend,optimization_level=0,seed_transpiler=seed)
    result=backend.run(compiled,shots=shots,seed_simulator=seed).result()
    if not result.success:
        raise RuntimeError("native shot execution failed")
    from qiskit.exceptions import QiskitError
    try:
        counts=result.get_counts()
    except QiskitError as exc:
        raise RuntimeError("native shot counts unavailable") from exc
    if len(qc.cregs)>1:
        # Register boundaries appear reversed in Qiskit memory labels.
        # Import requires contiguous, non-overlapping registers in bit order.
        sizes=tuple(len(reg) for reg in reversed(qc.cregs))
        if not isinstance(counts,Mapping):
            raise RuntimeError("unexpected native count schema")
        normalized={}
        for label,count in counts.items():
            if type(label) is not str or tuple(map(len,label.split(" ")))!=sizes:
                raise RuntimeError("unexpected native register-separated counts")
            key=label.replace(" ","")
            if key in normalized:
                raise RuntimeError("duplicate flattened count label")
            normalized[key]=count
        counts=normalized
    if (not isinstance(counts,Mapping) or any(type(label) is not str or len(label)!=qc.num_clbits or set(label)-{"0","1"}
        or type(count) is not int or count<=0 for label,count in counts.items()) or sum(counts.values())!=shots):
        raise RuntimeError("unexpected native count schema")
    from importlib.metadata import version
    measurements=tuple((i+1,qc.find_bit(item.qubits[0]).index,qc.find_bit(item.clbits[0]).index)
                       for i,item in enumerate(qc.data) if item.operation.name=="measure")
    return ShotResult(shots,qc.num_clbits,seed,tuple(sorted(counts.items())),measurements,
                      "qiskit-aer/statevector",version("qiskit-aer"))


def _dynamic_snapshot(template):
    _validate_dynamic(template)
    return template.copy()


def _validate_dynamic(template):
    from qiskit import QuantumCircuit
    from qiskit.circuit import Gate,Measure,Reset,IfElseOp,Clbit,ClassicalRegister
    from ._adapter import _validate_gate
    from ._validation import _angle
    if not isinstance(template,QuantumCircuit):
        raise TypeError("expected QuantumCircuit")
    if not 1<=template.num_qubits<=12 or not 1<=template.num_clbits<=12 or len(template.data)>1024:
        raise ResourceLimit("dynamic import exceeds 12 wires/bits or 1024 instructions")
    if template.parameters or template.metadata or template.layout is not None:
        raise UnsupportedOperation("dynamic import requires bound logical input without metadata/layout")
    if [bit for reg in template.cregs for bit in reg]!=list(template.clbits):
        raise UnsupportedOperation("classical registers must form an ordered disjoint bit partition")
    work=0
    def visit(block,depth):
        nonlocal work
        _angle(block.global_phase)
        if block.parameters or block.metadata or block.layout is not None:
            raise UnsupportedOperation("conditional block must be bound and logical")
        if block.num_qubits>12 or block.num_clbits>12:
            raise ResourceLimit("dynamic block exceeds 12 wires/bits")
        # No variable/expression-based control or captures in this subset.
        if getattr(block,"num_vars",0) or getattr(block,"num_stretches",0):
            raise UnsupportedOperation("dynamic variables and stretches are unsupported")
        for item in block.data:
            work+=1
            if work>1024:
                raise ResourceLimit("dynamic execution exceeds 1024 expanded instructions")
            op=item.operation
            if isinstance(op,Gate):
                if item.clbits:
                    raise UnsupportedOperation("unitary gate cannot have classical operands")
                _validate_gate(op)
            elif isinstance(op,IfElseOp):
                if depth>=3:
                    raise ResourceLimit("dynamic conditional depth exceeds three")
                condition=op.condition
                if not isinstance(condition,tuple) or len(condition)!=2:
                    raise UnsupportedOperation("only bit/register equality conditions are supported")
                target,value=condition
                if isinstance(target,Clbit):
                    width=1
                    if target not in block.clbits or target not in item.clbits:
                        raise UnsupportedOperation("condition must reference local instruction classical bits")
                elif isinstance(target,ClassicalRegister):
                    width=len(target)
                    if target not in block.cregs or any(bit not in item.clbits for bit in target):
                        raise UnsupportedOperation("condition must reference local instruction register")
                else:
                    raise UnsupportedOperation("unsupported condition target")
                if not isinstance(value,int) or not 0<=value<1<<width:
                    raise ValueError("invalid condition value")
                for body in op.blocks:
                    if body.num_qubits!=len(item.qubits) or body.num_clbits!=len(item.clbits):
                        raise UnsupportedOperation("conditional body operand width mismatch")
                    visit(body,depth+1)
            elif depth==0 and getattr(op,"base_class",None) in (Measure,Reset):
                pass
            else:
                raise UnsupportedOperation("unsupported native dynamic instruction or conditional measurement/reset")
    visit(template,0)
    return None


def _density_preflight(circuit,max_bytes):
    circuit._require_bound()
    n=circuit.num_qubits
    if n>8 or len(circuit._qc.data)>1024:
        raise ResourceLimit("density execution supports <=8 wires and 1024 instructions")
    _limit(2*n,3,budget=max_bytes)
    return n


def _run_density(circuit,initial_state,*,max_bytes):
    from qiskit.quantum_info import DensityMatrix
    n=_density_preflight(circuit,max_bytes)
    if initial_state is None:
        out=DensityMatrix.from_instruction(circuit._qc)
    else:
        if not isinstance(initial_state,DensityMatrix):
            raise TypeError("initial_state must be a native DensityMatrix")
        if initial_state.num_qubits!=n or initial_state.data.shape!=(1<<n,1<<n):
            raise ValueError("density matrix width mismatch")
        if not initial_state.is_valid(atol=1e-9,rtol=0):
            raise ValueError("initial density matrix must be positive and trace one")
        out=DensityMatrix(initial_state.data.copy()).evolve(circuit._qc)
    if not out.is_valid(atol=1e-9,rtol=0):
        raise ArithmeticError("native density evolution returned invalid state")
    return DensityMatrix(out.data.copy())


def _run_noisy(circuit,noise_model,*,seed,max_bytes):
    from qiskit import transpile
    from qiskit.quantum_info import DensityMatrix
    _density_preflight(circuit,max_bytes)
    if seed is not None:
        seed=_int(seed)
        if seed>2**32-1:
            raise ValueError("seed exceeds unsigned 32-bit range")
    try:
        from qiskit_aer import AerSimulator
        from qiskit_aer.noise import NoiseModel
    except ImportError as exc:
        raise UnsupportedOperation("install ketary[dynamic] for local noise simulation") from exc
    if not isinstance(noise_model,NoiseModel):
        raise TypeError("expected native Aer NoiseModel")
    backend=AerSimulator(method="density_matrix",noise_model=noise_model,max_parallel_threads=1)
    raw=circuit.to_qiskit()
    raw.save_density_matrix()
    compiled=transpile(raw,backend=backend,optimization_level=0,seed_transpiler=seed)
    result=backend.run(compiled,shots=1,seed_simulator=seed).result()
    if not result.success:
        raise RuntimeError("native noisy density execution failed")
    out=DensityMatrix(result.data(0)["density_matrix"])
    if out.num_qubits!=circuit.num_qubits or not out.is_valid(atol=1e-9,rtol=0):
        raise ArithmeticError("native noise simulation returned invalid density")
    return DensityMatrix(out.data.copy())


def _run_channel(circuit,channel,initial_state,*,wires=None,max_bytes):
    """Trusted native Kraus data; exact-in-model density evolution, no Aer."""
    from math import isfinite
    from qiskit.quantum_info import Kraus,DensityMatrix
    n=_density_preflight(circuit,max_bytes)
    if wires is None:
        if n>4:
            raise ResourceLimit("full-width Kraus channel execution supports <=4 wires")
        width=n
        selected=None
    else:
        from collections.abc import Mapping
        from itertools import islice
        if isinstance(wires,(str,bytes,set,frozenset,Mapping)):
            raise ValueError("expected ordered channel wires")
        try:
            selected=tuple(_int(w) for w in islice(iter(wires),5))
        except TypeError as exc:
            raise ValueError("expected ordered channel wires") from exc
        width=len(selected)
        if width>4:
            raise ResourceLimit("local Kraus channel supports <=4 wires")
        if not width or len(set(selected))!=width or any(w>=n for w in selected):
            raise ValueError("expected nonempty distinct channel wires in range")
    if not isinstance(channel,Kraus):
        raise TypeError("expected native Kraus channel")
    dim=(2,)*width
    if channel.input_dims()!=dim or channel.output_dims()!=dim:
        raise ValueError("channel must preserve selected qubit dimensions")
    matrices=channel.data
    if not isinstance(matrices,list) or not 1<=len(matrices)<=16:
        raise UnsupportedOperation("expected 1..16 standard Kraus operators")
    if 16*(3*(1<<(2*n))+len(matrices)*(1<<(2*width)))>max_bytes:
        raise ResourceLimit("density and Kraus payload budget exceeded")
    for matrix in matrices:
        if matrix.shape!=(1<<width,1<<width) or any(
            not isfinite(z.real) or not isfinite(z.imag) for z in matrix.flat
        ):
            raise ValueError("Kraus operators must be finite square matrices")
    owned=Kraus([m.copy() for m in matrices],input_dims=dim,output_dims=dim)
    if not owned.is_cptp(atol=1e-9,rtol=0):
        raise ValueError("channel must be completely positive and trace preserving")
    state=_run_density(circuit,initial_state,max_bytes=max_bytes)
    if selected is None:
        result=state.evolve(owned)
    else:
        result=state.evolve(owned,qargs=list(selected))
    if result.num_qubits!=n or not result.is_valid(atol=1e-9,rtol=0):
        raise ArithmeticError("native channel returned invalid density")
    return DensityMatrix(result.data.copy(),dims=(2,)*n)
