"""Phase-preserving logical simplification of the supported native subset.

This is not a compiler or a device-aware transpiler. Only exactly adjacent
inverse pairs on identically ordered wires are removed.
"""
from ._adapter import _validate

_FIXED_INVERSES={
    "h":"h","x":"x","y":"y","z":"z","cx":"cx","cz":"cz",
    "swap":"swap","ccx":"ccx","s":"sdg","sdg":"s","t":"tdg","tdg":"t",
}
_ROTATIONS={"rx","ry","rz"}

def _inverse_pair(a,b):
    if a.qubits!=b.qubits:
        return False
    x,y=a.operation,b.operation
    if x.name in _FIXED_INVERSES:
        return y.name==_FIXED_INVERSES[x.name]
    if x.name in _ROTATIONS and x.name==y.name:
        # Exact numeric opposites only. Do not reduce modulo 2*pi:
        # R(2*pi)=-I, which matters in controlled contexts.
        return float(x.params[0])==-float(y.params[0])
    return False

def _cancel_adjacent(qc):
    _validate(qc)
    stack=[]
    for instruction in qc.data:
        if stack and _inverse_pair(stack[-1],instruction):
            stack.pop()
        else:
            stack.append(instruction)
    optimized=qc.copy_empty_like()
    optimized.global_phase=qc.global_phase
    for instruction in stack:
        wires=[qc.find_bit(w).index for w in instruction.qubits]
        optimized.append(instruction.operation,wires,copy=True)
    return optimized
