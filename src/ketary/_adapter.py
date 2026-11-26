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
    if allow_parameters and getattr(qc.global_phase,"parameters",()):
        _gate_angle(qc.global_phase,allow_parameters=True)
    elif not math.isfinite(float(qc.global_phase)):
        raise ValueError("invalid global phase")


def _bound_validation_indices(qc):
    """Call-local sweep plan for a validated native template.

    Native assignment changes only symbolic slots and global phase. Validate
    unchanged numeric slots once; inspect every affected instruction per row.
    Dense templates keep the original mapping/full scan. Abort discovery
    as soon as more than half of the instructions are affected.
    No plan or mutable native circuit is cached between public calls.
    """
    data=qc.data
    affected=[]
    threshold=len(data)//2
    for i,item in enumerate(data):
        symbolic=False
        for value in item.params:
            if getattr(value,"parameters",()):
                symbolic=True
            else:
                _angle(value)
        if symbolic:
            affected.append(i)
            if len(affected)>threshold:
                return None
    return tuple(affected)


def _validate_bound_values(qc,indices=None):
    """Assignment on an already validated, exclusively owned unitary circuit.

    Native assign_parameters preserves instruction kind, operands and layout.
    Evaluated expressions still require finite real checks. External native
    imports must use the complete _validate gate/metadata allowlist.
    """
    if qc.parameters:
        raise UnsupportedOperation("bind all symbolic parameters before this operation")
    data=qc.data
    for item in (data if indices is None else (data[i] for i in indices)):
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
    """Append validated bound or symbolic placements in one suffix/phase transaction.

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


def _validate_annotation_metadata(metadata):
    """Validate trusted JSON-like metadata without arbitrary serialization hooks."""
    import json
    from ._validation import ResourceLimit
    if type(metadata) is not dict:
        raise ValueError("expected ordinary metadata dictionary")
    nodes=0
    def visit(value,depth):
        nonlocal nodes
        nodes+=1
        if nodes>4096 or depth>8:
            raise ResourceLimit("metadata exceeds node or depth budget")
        kind=type(value)
        if kind is dict:
            if len(value)>4096-nodes:
                raise ResourceLimit("metadata exceeds node budget")
            for key,child in value.items():
                if type(key) is not str:
                    raise ValueError("metadata keys must be strings")
                visit(key,depth+1)
                visit(child,depth+1)
        elif kind is list:
            if len(value)>4096-nodes:
                raise ResourceLimit("metadata exceeds node budget")
            for child in value:
                visit(child,depth+1)
        elif kind is str:
            if len(value)>4096:
                raise ResourceLimit("metadata string exceeds length budget")
            try:
                value.encode("utf-8")
            except UnicodeError as exc:
                raise ValueError("metadata strings must be valid UTF-8") from exc
        elif kind is int:
            if value.bit_length()>64:
                raise ResourceLimit("metadata integer exceeds 64 bits")
        elif kind is float:
            if not math.isfinite(value):
                raise ValueError("metadata numbers must be finite")
        elif kind is bool or value is None:
            pass
        else:
            raise ValueError("metadata must contain only JSON-compatible builtins")
    visit(metadata,0)
    if len(json.dumps(metadata,ensure_ascii=False,allow_nan=False,separators=(",",":")).encode("utf-8"))>65536:
        raise ResourceLimit("metadata exceeds 64 KiB")

def _project_annotated(template):
    """Return independent native structural snapshot and ideal-only projection."""
    from qiskit.circuit import Barrier
    from ._validation import ResourceLimit
    QC,_=_sdk()
    if not isinstance(template,QC):
        raise TypeError("expected QuantumCircuit")
    if not 1<=template.num_qubits<=22 or len(template.data)>10000:
        raise ResourceLimit("annotated projection exceeds 22 wires or 10000 instructions")
    if template.num_clbits or template.parameters or template.layout is not None or getattr(template,"num_vars",0) or getattr(template,"num_stretches",0):
        raise UnsupportedOperation("annotated projection requires bound logical unitary input")
    _angle(template.global_phase)
    _validate_annotation_metadata(template.metadata)
    # Validate the entire source before allocating either returned circuit.
    for item in template.data:
        if item.clbits:
            raise UnsupportedOperation("classical operands unsupported")
        op=item.operation
        if type(op) is Barrier:
            if op.params or not item.qubits or len(set(item.qubits))!=len(item.qubits) or op.num_qubits!=len(item.qubits):
                raise UnsupportedOperation("invalid native barrier")
        else:
            _validate_gate(op)
    source=template.copy()
    # Explicitly independent logical projection: no native annotation or
    # scheduling equivalence is claimed for this output.
    logical=QC(source.num_qubits,global_phase=source.global_phase)
    for item in source.data:
        if type(item.operation) is not Barrier:
            logical.append(item.operation,[source.find_bit(w).index for w in item.qubits],copy=True)
    _validate(logical)
    return logical,source
