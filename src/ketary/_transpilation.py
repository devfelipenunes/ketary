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
    if not float(abs(Operator(raw).data-reference.data).max())<=1e-9:
        raise UnsupportedOperation("strict synthesized operator residual exceeds tolerance")
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
    raw=QuantumCircuit(controls+circuit.num_qubits)
    raw.append(circuit.to_qiskit().to_gate().control(controls,ctrl_state=state,annotated=False),range(raw.num_qubits))
    return _synthesize_native(raw,seed=seed)
