"""Narrow, explicitly checked Qiskit transpilation experiment."""
from ._validation import _int, ResourceLimit, UnsupportedOperation

from ._gate_specs import SPECS
_BASIS=frozenset(SPECS)

def _lower(circuit, *, basis_gates, seed):
    if circuit.num_qubits>8:
        raise ResourceLimit("verified logical transpilation limited to eight qubits")
    if isinstance(basis_gates,str):
        raise ValueError("basis_gates must be a sequence of gate names")
    from itertools import islice
    names=tuple(islice(iter(basis_gates),len(_BASIS)+1))
    if not names or any(type(n) is not str or n not in _BASIS for n in names) or len(set(names))!=len(names):
        raise ValueError("basis must contain unique supported gate names")
    seed=_int(seed)
    if seed>2**32-1:
        raise ValueError("seed exceeds unsigned 32-bit range")
    from qiskit import transpile
    from qiskit.transpiler.exceptions import TranspilerError
    from ._circuit import Circuit
    try:
        # Logical equivalence is for arbitrary input, not only clean ancillas.
        raw=transpile(circuit.to_qiskit(),basis_gates=list(names),optimization_level=0,
                      seed_transpiler=seed,qubits_initially_zero=False)
    except TranspilerError as exc:
        raise UnsupportedOperation("Qiskit could not lower to the requested logical basis") from exc
    lowered=Circuit._from_native(raw,owned=True)
    if any(item.operation.name not in names for item in raw.data):
        raise UnsupportedOperation("transpiler emitted a gate outside the requested basis")
    if circuit.test.equivalent(lowered,ignore_global_phase=False,atol=1e-9).status!="PASS":
        raise UnsupportedOperation("strict operator equivalence was not verified")
    return lowered


def _synthesize_native(template,*,seed):
    """Trusted local gate-only input; strict full operator qualification."""
    from qiskit import QuantumCircuit,transpile
    from qiskit.circuit import Gate
    from qiskit.quantum_info import Operator
    from qiskit.transpiler.exceptions import TranspilerError
    from ._circuit import Circuit
    if not isinstance(template,QuantumCircuit):
        raise TypeError("expected QuantumCircuit")
    if not 1<=template.num_qubits<=5 or len(template.data)>256:
        raise ResourceLimit("synthesis supports 1..5 wires and <=256 input instructions")
    seed=_int(seed)
    if seed>2**32-1:
        raise ValueError("seed exceeds unsigned 32-bit range")
    if template.num_clbits or template.parameters or template.metadata or template.layout is not None:
        raise UnsupportedOperation("synthesis requires bound logical input without metadata/layout")
    if any(not isinstance(item.operation,Gate) or item.clbits for item in template.data):
        raise UnsupportedOperation("synthesis cannot discard nonunitary instructions or barriers")
    source=template.copy()
    reference=Operator(source)
    if not reference.is_unitary(atol=1e-9,rtol=0):
        raise ValueError("native operator must be finite and unitary")
    try:
        raw=transpile(source,basis_gates=["u","cx"],optimization_level=0,
                      seed_transpiler=seed,qubits_initially_zero=False)
    except TranspilerError as exc:
        raise UnsupportedOperation("native synthesis could not reach logical basis") from exc
    if len(raw.data)>10000:
        raise ResourceLimit("synthesis exceeds 10000 output instructions")
    result=Circuit._from_native(raw,owned=True)
    if any(item.operation.name not in ("u","cx") for item in raw.data):
        raise UnsupportedOperation("synthesis emitted noncanonical gates")
    # Retain the evaluated output matrix only for this qualification.
    # Fallback diagnostics use the same already-qualified native output.
    actual=Operator(raw).data
    residual=float(abs(actual-reference.data).max())
    if not residual<=1e-9:
        # The default native synthesis can approximate near-special Weyl
        # classes. For a single bounded Hamiltonian, qualify one alternative
        # native decomposition. Never accept a merely phase-equivalent result.
        from cmath import exp, phase as complex_phase
        from qiskit.circuit.library import HamiltonianGate, Isometry
        # Reuse the evaluated output and its residual.
        phase=complex_phase(sum(complex(a).conjugate()*complex(b)
                                for a,b in zip(actual.flat,reference.data.flat)))
        aligned_residual=float(abs(actual*exp(1j*phase)-reference.data).max())
        if (3<=source.num_qubits<=5 and len(source.data)==1
                and isinstance(source.data[0].operation,HamiltonianGate)):
            alternative=QuantumCircuit(source.num_qubits)
            alternative.append(Isometry(reference.data,0,0,epsilon=1e-12),
                               range(source.num_qubits))
            try:
                candidate=transpile(alternative,basis_gates=["u","cx"],
                                    optimization_level=0,seed_transpiler=seed,
                                    qubits_initially_zero=False)
            except TranspilerError as exc:
                raise UnsupportedOperation("alternative Hamiltonian synthesis failed") from exc
            if len(candidate.data)>10000:
                raise ResourceLimit("alternative synthesis exceeds 10000 output instructions")
            if (candidate.num_qubits!=source.num_qubits or candidate.num_clbits
                    or any(item.operation.name not in ("u","cx") for item in candidate.data)):
                raise UnsupportedOperation("alternative synthesis emitted noncanonical gates")
            candidate_matrix=Operator(candidate).data
            candidate_phase=complex_phase(sum(complex(a).conjugate()*complex(b)
                for a,b in zip(candidate_matrix.flat,reference.data.flat)))
            candidate.global_phase+=candidate_phase
            if float(abs(Operator(candidate).data-reference.data).max())<=1e-9:
                return Circuit._from_native(candidate,owned=True)
        raise UnsupportedOperation(
            "strict synthesized operator residual exceeds tolerance "
            f"(residual={residual:.17g}, phase_aligned_residual={aligned_residual:.17g}, "
            f"phase={phase:.17g}, wires={source.num_qubits}, seed={seed}, gates={len(raw.data)})"
        )
    return result


def _control_block(circuit,*,controls,control_state,seed):
    from qiskit import QuantumCircuit
    circuit._require_bound()
    controls=_int(controls,1)
    if circuit.num_qubits+controls>5 or len(circuit._qc.data)>256:
        raise ResourceLimit("controlled synthesis supports <=5 total wires, <=256 source gates")
    state=(1<<controls)-1 if control_state is None else _int(control_state)
    if state>=1<<controls:
        raise ValueError("control state exceeds control width")
    seed=_int(seed)
    if seed>2**32-1:
        raise ValueError("seed exceeds unsigned 32-bit range")
    raw=QuantumCircuit(controls+circuit.num_qubits)
    raw.append(circuit.to_qiskit().to_gate().control(controls,ctrl_state=state,annotated=False),range(raw.num_qubits))
    # Closed/open single control over X-only blocks (including empty
    # phase-only blocks): source phase becomes a phase on the control.
    # Retain canonical u,cx output and strict whole-operator qualification.
    if controls==1 and all(item.operation.name=="x" for item in circuit._qc.data):
        from qiskit.quantum_info import Operator
        from ._circuit import Circuit
        candidate=QuantumCircuit(raw.num_qubits)
        if state==0:
            candidate.u(3.141592653589793,0,3.141592653589793,0)
        phase=float(circuit._qc.global_phase)
        if phase:
            candidate.u(0,0,phase,0)
        for item in circuit._qc.data:
            candidate.cx(0,1+circuit._qc.find_bit(item.qubits[0]).index)
        if state==0:
            candidate.u(3.141592653589793,0,3.141592653589793,0)
        if float(abs(Operator(candidate).data-Operator(raw).data).max())<=1e-9:
            return Circuit._from_native(candidate,owned=True)
    return _synthesize_native(raw,seed=seed)


def _transpile_for(circuit,backend,*,optimization_level,seed):
    from qiskit import transpile
    from qiskit.providers import BackendV2
    from qiskit.transpiler.exceptions import TranspilerError
    if not isinstance(backend,BackendV2):
        raise TypeError("expected explicit native BackendV2")
    if circuit.parameters:
        raise UnsupportedOperation("bind parameters before target transpilation")
    if circuit.num_qubits>12 or len(circuit._qc.data)>1024:
        raise ResourceLimit("target transpilation supports <=12 logical wires, 1024 instructions")
    level,seed=_int(optimization_level),_int(seed)
    if level>3 or seed>2**32-1:
        raise ValueError("invalid optimization level or seed")
    if circuit.num_qubits>backend.num_qubits:
        raise ResourceLimit("target has too few qubits")
    try:
        return transpile(circuit.to_qiskit(),backend=backend,optimization_level=level,
                         seed_transpiler=seed,qubits_initially_zero=False)
    except TranspilerError as exc:
        raise UnsupportedOperation("target cannot transpile requested circuit") from exc


def _finite_complex(value):
    from numbers import Complex
    from math import isfinite
    if isinstance(value,bool) or not isinstance(value,Complex):
        raise ValueError("expected finite complex scalar")
    z=complex(value)
    if not isfinite(z.real) or not isfinite(z.imag):
        raise ValueError("expected finite complex scalar")
    return z


def _bounded_rows(values,limit):
    from itertools import islice
    from collections.abc import Mapping
    if isinstance(values,(str,bytes,Mapping,set,frozenset)):
        raise TypeError("expected ordered numeric iterable")
    try:
        out=tuple(islice(iter(values),limit+1))
    except TypeError as exc:
        raise TypeError("expected ordered numeric iterable") from exc
    if len(out)>limit:
        raise ResourceLimit("dense synthesis supports at most 32 amplitudes or rows")
    return out


def _dense_width(size):
    if size<2 or size&(size-1):
        raise ValueError("dense dimension must be 2**n, n>=1")
    return size.bit_length()-1


def _prepare_state(amplitudes,*,seed):
    from math import fsum
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import StatePreparation
    values=tuple(_finite_complex(v) for v in _bounded_rows(amplitudes,32))
    n=_dense_width(len(values))
    try:
        norm=fsum(v.real*v.real+v.imag*v.imag for v in values)
    except OverflowError as exc:
        raise ValueError("state amplitudes must be normalized") from exc
    if not abs(norm-1)<=1e-10:
        raise ValueError("state amplitudes must be normalized; no implicit normalization")
    raw=QuantumCircuit(n)
    raw.append(StatePreparation(list(values),normalize=False),range(n))
    return _synthesize_native(raw,seed=seed)


def _from_unitary(matrix,*,seed):
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import UnitaryGate
    from qiskit.quantum_info import Operator
    rows=_bounded_rows(matrix,32)
    n=_dense_width(len(rows))
    values=tuple(tuple(_finite_complex(v) for v in _bounded_rows(row,32)) for row in rows)
    if any(len(row)!=len(rows) for row in values):
        raise ValueError("expected a square unitary matrix")
    operator=Operator([list(row) for row in values])
    if not operator.is_unitary(atol=1e-10,rtol=0):
        raise ValueError("matrix must be unitary")
    raw=QuantumCircuit(n)
    raw.append(UnitaryGate(operator),range(n))
    return _synthesize_native(raw,seed=seed)


def _evolve_dense(circuit,observable,*,time,seed):
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import HamiltonianGate
    from ._observable import Observable
    from ._validation import _angle
    circuit._require_bound()
    if not isinstance(observable,Observable):
        raise TypeError("expected Observable")
    n=circuit.num_qubits
    if n>5:
        raise ResourceLimit("dense Hamiltonian evolution supports <=5 wires")
    t=_angle(time)
    # Materialize only a bounded 32x32 Hermitian operator.
    H=observable.to_qiskit(n).to_matrix()
    raw=QuantumCircuit(n)
    raw.append(HamiltonianGate(H,t),range(n))
    block=_synthesize_native(raw,seed=seed)
    return circuit.apply(block)
