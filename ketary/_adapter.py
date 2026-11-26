"""Strict Qiskit interop for the experimental unitary subset."""
from __future__ import annotations
import math
from ._validation import UnsupportedOperation

def _sdk():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    return QuantumCircuit, Statevector

def _validate(qc):
    QC,_=_sdk()
    from qiskit.circuit.library import HGate,XGate,ZGate,CXGate,SwapGate
    if not isinstance(qc,QC):
        raise TypeError("expected QuantumCircuit")
    if qc.num_qubits<1 or qc.num_clbits or qc.parameters or getattr(qc,"layout",None) is not None or qc.metadata:
        raise UnsupportedOperation("PoC supports only unparameterized logical quantum circuits without metadata/classical bits/layout")
    allowed=(HGate,XGate,ZGate,CXGate,SwapGate)
    for item in qc.data:
        if item.operation.base_class not in allowed or item.operation.params or item.clbits:
            raise UnsupportedOperation(f"unsupported operation: {item.operation.name}")
        if item.operation.base_class is CXGate and item.operation.ctrl_state != 1:
            raise UnsupportedOperation("open-control CX is outside the PoC whitelist")
    if not math.isfinite(float(qc.global_phase)):
        raise ValueError("invalid global phase")
