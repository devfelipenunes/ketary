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
        raw=transpile(circuit.to_qiskit(),basis_gates=list(names),optimization_level=0,seed_transpiler=seed)
    except TranspilerError as exc:
        raise UnsupportedOperation("Qiskit could not lower to the requested logical basis") from exc
    lowered=Circuit._from_native(raw,owned=True)
    if any(item.operation.name not in names for item in raw.data):
        raise UnsupportedOperation("transpiler emitted a gate outside the requested basis")
    if circuit.test.equivalent(lowered,ignore_global_phase=False,atol=1e-9).status!="PASS":
        raise UnsupportedOperation("strict operator equivalence was not verified")
    return lowered
