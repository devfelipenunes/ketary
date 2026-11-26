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
