"""Explicit bounded ideal-state trace."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from ._adapter import _sdk
from ._validation import _int, _limit, _tol, ResourceLimit
from ._result import Result, CheckResult

@dataclass(frozen=True)
class TraceStep:
    operation: str
    wires: tuple[int,...]
    result: Result

@dataclass(frozen=True)
class TraceComparison:
    """First observed state divergence at explicitly aligned gate indices."""
    check: CheckResult
    step_index: int | None = None
    actual_operation: str | None = None
    reference_operation: str | None = None
    actual_wires: tuple[int,...] | None = None
    reference_wires: tuple[int,...] | None = None

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

    def compare(self,reference,*,ignore_global_phase=True,atol=1e-9,
                max_bytes=64*1024**2,max_steps=256):
        """Compare states at equal-index checkpoints, not gate identities.

        The caller must establish meaningful alignment. This reports the
        first observed divergence, not a proof of the root cause. A matching
        trace covers only the zero-input trajectory, not operator equivalence.
        """
        from ._circuit import Circuit
        if not isinstance(reference,Circuit):
            raise TypeError("expected Circuit reference")
        t=_tol(atol)
        steps=_int(max_steps)
        budget=_int(max_bytes,1)
        if type(ignore_global_phase) is not bool:
            raise ValueError("ignore_global_phase must be bool")
        a,b=self._c,reference
        if a.num_qubits!=b.num_qubits or len(a._qc.data)!=len(b._qc.data):
            return TraceComparison(CheckResult("UNSUPPORTED",None,None,t,
                "checkpoint alignment requires equal qubit and operation counts"))
        count=len(a._qc.data)
        try:
            if a.num_qubits>8 or count>steps:
                raise ResourceLimit("trace comparison exceeds qubit or step limit")
            _limit(a.num_qubits,2*(count+1),budget=budget)
        except ResourceLimit as exc:
            return TraceComparison(CheckResult("UNSUPPORTED",None,None,t,str(exc)))
        actual=a.debug.trace(max_bytes=budget,max_steps=steps)
        expected=b.debug.trace(max_bytes=budget,max_steps=steps)
        largest=0.0
        for i,(x,y) in enumerate(zip(actual,expected,strict=True)):
            check=x.result.test.state(y.result,ignore_global_phase=ignore_global_phase,atol=t)
            largest=max(largest,check.actual)
            if check.status=="FAIL":
                return TraceComparison(check,i,x.operation,y.operation,x.wires,y.wires)
        return TraceComparison(CheckResult("PASS",largest,0,t,
            "all aligned zero-input checkpoints match"))
