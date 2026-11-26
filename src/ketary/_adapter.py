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

def _validate_gate(gate,*,allow_parameters=False):
    Gate,classes=_gate_classes()
    from qiskit.circuit.library import MCXGate
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

def _validate(qc):
    QC,_=_sdk()
    if not isinstance(qc,QC):
        raise TypeError("expected QuantumCircuit")
    if qc.num_qubits<1 or qc.num_clbits or qc.parameters or getattr(qc,"layout",None) is not None or qc.metadata:
        raise UnsupportedOperation("L0 supports logical circuits with bound real parameters and without metadata/classical bits/layout")
    for item in qc.data:
        if item.clbits:
            raise UnsupportedOperation("classical operands unsupported")
        _validate_gate(item.operation)
    if not math.isfinite(float(qc.global_phase)):
        raise ValueError("invalid global phase")
