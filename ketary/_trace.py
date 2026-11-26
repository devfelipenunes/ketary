"""Explicit bounded ideal-state trace."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from ._adapter import _sdk
from ._validation import _int, _limit, ResourceLimit
from ._result import Result

@dataclass(frozen=True)
class TraceStep:
    operation: str
    wires: tuple[int,...]
    result: Result

class _Debug:
    def __init__(self,c):
        self._c=c

    def trace(self,*,max_bytes=64*1024**2,max_steps=256):
        qc=self._c._qc
        if qc.num_qubits > 8:
            raise ResourceLimit("trace supports at most eight qubits in PoC")
        if len(qc.data)>_int(max_steps):
            raise ResourceLimit("trace step limit exceeded")
        _limit(qc.num_qubits,len(qc.data)+1,budget=max_bytes)
        _,SV=_sdk()
        a=np.zeros(1<<qc.num_qubits,dtype=complex)
        a[0]=np.exp(1j*float(qc.global_phase))
        state=SV(a)
        steps=[TraceStep("initial (global phase applied)",(),Result(state.data))]
        for item in qc.data:
            wires=tuple(qc.find_bit(w).index for w in item.qubits)
            state=state.evolve(item.operation,qargs=list(wires))
            steps.append(TraceStep(item.operation.name,wires,Result(state.data)))
        return tuple(steps)
