"""Strict Qiskit interop for the L0 unitary gate subset."""
from __future__ import annotations
import math
from functools import lru_cache
from ._validation import UnsupportedOperation, _angle

def _sdk():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    return QuantumCircuit, Statevector

from ._gate_specs import SPECS

@lru_cache(maxsize=1)
def _gate_classes():
    from qiskit.circuit import Gate
    from qiskit.circuit import library
    return Gate,{getattr(library,spec[0]):(name,spec) for name,spec in SPECS.items()}

@lru_cache(maxsize=1)
def _mcx_class():
    from qiskit.circuit.library import MCXGate
    return MCXGate

def _validate_gate(gate,*,allow_parameters=False):
    Gate,classes=_gate_classes()
    MCXGate=_mcx_class()
    from ._gate_specs import MCX_MIN_WIRES,MCX_MAX_WIRES
    if isinstance(gate,Gate) and gate.base_class is MCXGate:
        if (gate.name!="mcx" or not MCX_MIN_WIRES<=gate.num_qubits<=MCX_MAX_WIRES
            or gate.params or gate.num_ctrl_qubits!=gate.num_qubits-1
            or gate.ctrl_state!=(1<<gate.num_ctrl_qubits)-1):
            raise UnsupportedOperation("MCX requires 3..7 distinct closed controls")
        return
    if not isinstance(gate,Gate) or gate.base_class not in classes:
        raise UnsupportedOperation("only supported standard unitary gates can be appended/imported")
    name,(_,wires,params,controls,_)=classes[gate.base_class]
    if gate.name!=name or gate.num_qubits!=wires:
        raise UnsupportedOperation("noncanonical gate name or width")
    if len(gate.params)!=params:
        raise UnsupportedOperation("invalid gate parameter count")
    for value in gate.params:
        _gate_angle(value,allow_parameters=allow_parameters)
    if controls and gate.ctrl_state!=(1<<controls)-1:
        raise UnsupportedOperation("open controls are outside the logical whitelist")

def _gate_angle(value,*,allow_parameters=False):
    if allow_parameters:
        from qiskit.circuit import ParameterExpression
        if isinstance(value,ParameterExpression) and value.parameters:
            return value
    return _angle(value)

def _validate(qc,*,allow_parameters=False):
    QC,_=_sdk()
    if not isinstance(qc,QC):
        raise TypeError("expected QuantumCircuit")
    if qc.num_qubits<1 or qc.num_clbits or (qc.parameters and not allow_parameters) or getattr(qc,"layout",None) is not None or qc.metadata:
        raise UnsupportedOperation("L0 supports logical circuits with bound real parameters and without metadata/classical bits/layout")
    for item in qc.data:
        if item.clbits:
            raise UnsupportedOperation("classical operands unsupported")
        _validate_gate(item.operation,allow_parameters=allow_parameters)
    if not math.isfinite(float(qc.global_phase)):
        raise ValueError("invalid global phase")


def _validate_bound_values(qc):
    """Assignment on an already validated, exclusively owned unitary circuit.

    Native assign_parameters preserves instruction kind, operands and layout.
    Evaluated expressions still require finite real checks. External native
    imports must use the complete _validate gate/metadata allowlist.
    """
    if qc.parameters:
        raise UnsupportedOperation("bind all symbolic parameters before this operation")
    for item in qc.data:
        for value in item.params:
            # CircuitInstruction exposes native parameters without constructing
            # a Python Gate. Exact floats are the ordinary native numeric case.
            if type(value) is float:
                if not math.isfinite(value):
                    raise ValueError("rotation angle must be finite")
            else:
                _angle(value)
    if not math.isfinite(float(qc.global_phase)):
        raise ValueError("invalid global phase")


def _append_bound_blocks(target,block,placements):
    """Append validated ordered placements in one suffix/phase transaction.

    The caller preflights mappings and bounds. No concurrent mutation
    guarantee. Self-application uses one independent source snapshot.
    Return whether any intermediate native global phase changed.
    """
    start=len(target.data)
    phase=target.global_phase
    source=block.copy() if target is block else block
    changed=False
    try:
        for wires in placements:
            before=target.global_phase
            target.compose(source,qubits=list(wires),inplace=True)
            changed=changed or target.global_phase!=before
    except Exception:
        del target.data[start:]
        target.global_phase=phase
        raise
    return changed


def _append_bound_block(target,block,wires):
    """Append one validated bound block; shared transaction implementation."""
    return _append_bound_blocks(target,block,(wires,))
