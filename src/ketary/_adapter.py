"""Strict Qiskit interop for the L0 unitary gate subset."""
from __future__ import annotations
import math
from functools import lru_cache
from ._validation import UnsupportedOperation, _angle

def _sdk():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    return QuantumCircuit, Statevector

@lru_cache(maxsize=1)
def _gate_classes():
    from qiskit.circuit import Gate
    from qiskit.circuit.library import (
        HGate, XGate, YGate, ZGate, SGate, SdgGate, TGate, TdgGate,
        RXGate, RYGate, RZGate, CXGate, CZGate, SwapGate, CCXGate,
    )
    return (Gate, (HGate,XGate,YGate,ZGate,SGate,SdgGate,TGate,TdgGate,
                   CXGate,CZGate,SwapGate,CCXGate),
            (RXGate,RYGate,RZGate), {CXGate:1,CZGate:1,CCXGate:3})

def _validate_gate(gate):
    Gate,fixed,rotations,controls=_gate_classes()
    if not isinstance(gate,Gate) or gate.base_class not in fixed+rotations:
        raise UnsupportedOperation("only supported standard unitary gates can be appended/imported")
    cls=gate.base_class
    if cls in rotations:
        if len(gate.params)!=1:
            raise UnsupportedOperation("invalid rotation parameters")
        _angle(gate.params[0])
    elif gate.params:
        raise UnsupportedOperation("unexpected gate parameters")
    if cls in controls and gate.ctrl_state!=controls[cls]:
        raise UnsupportedOperation("open-control gates are outside the L0 whitelist")

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
