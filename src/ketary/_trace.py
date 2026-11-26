"""Explicit bounded ideal-state trace."""
from __future__ import annotations
from dataclasses import dataclass, asdict
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

    def to_dict(self):
        record=asdict(self)
        for field in ('actual_wires','reference_wires'):
            if record[field] is not None: record[field]=list(record[field])
        record['scope']='aligned zero-input checkpoints, not root cause'
        return record

class _Debug:
    def __init__(self,c):
        self._c=c

    def trace(self,*,max_bytes=64*1024**2,max_steps=256):
        self._c._require_bound()
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

    def checkpoint(self,index,*,max_bytes=64*1024**2,max_steps=256):
        """Explicit zero-input evolution through one requested checkpoint."""
        self._c._require_bound()
        qc=self._c._qc
        index=_int(index)
        if index>len(qc.data):
            raise ValueError("checkpoint outside circuit")
        if qc.num_qubits>8 or index>_int(max_steps):
            raise ResourceLimit("checkpoint limit exceeded")
        _limit(qc.num_qubits,budget=max_bytes)
        _,SV=_sdk()
        a=np.zeros(1<<qc.num_qubits,dtype=complex)
        a[0]=np.exp(1j*float(qc.global_phase))
        state=SV(a)
        operation="initial (global phase applied)"
        wires=()
        for i in range(index):
            item=qc.data[i]
            wires=tuple(qc.find_bit(w).index for w in item.qubits)
            operation=item.operation.name
            state=state.evolve(item.operation,qargs=list(wires))
        return TraceStep(operation,wires,Result(state.data))

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
        a._require_bound()
        b._require_bound()
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
        # Preserve the historical conservative budget contract, but evolve
        # only two current states and stop at the first observed divergence.
        def checkpoints(c):
            _,SV=_sdk()
            initial=np.zeros(1<<c.num_qubits,dtype=complex)
            initial[0]=np.exp(1j*float(c._qc.global_phase))
            state=SV(initial)
            yield TraceStep("initial (global phase applied)",(),Result(state.data))
            for item in c._qc.data:
                wires=tuple(c._qc.find_bit(w) for w in item.qubits)
                state=state.evolve(item.operation,qargs=[w.index for w in wires])
                yield TraceStep(item.operation.name,tuple(w.index for w in wires),Result(state.data))
        actual=checkpoints(a)
        expected=checkpoints(b)
        largest=0.0
        for i,(x,y) in enumerate(zip(actual,expected,strict=True)):
            check=x.result.test.state(y.result,ignore_global_phase=ignore_global_phase,atol=t)
            largest=max(largest,check.actual)
            if check.status=="FAIL":
                return TraceComparison(check,i,x.operation,y.operation,x.wires,y.wires)
        return TraceComparison(CheckResult("PASS",largest,0,t,
            "all aligned zero-input checkpoints match"))


    def compare_checkpoints(self,reference,pairs,*,ignore_global_phase=True,atol=1e-9,
                            max_bytes=64*1024**2,max_steps=256):
        """Compare explicitly supplied (observed, reference) checkpoint indices.

        Different circuit lengths are allowed. Alignment is caller-provided,
        not inferred. At most 32 strictly increasing index pairs; an index
        may repeat on one side. Each requested prefix is explicitly evolved.
        """
        from itertools import islice
        from ._circuit import Circuit
        if not isinstance(reference,Circuit):
            raise TypeError("expected Circuit reference")
        a,b=self._c,reference
        a._require_bound()
        b._require_bound()
        tolerance=_tol(atol)
        budget=_int(max_bytes,1)
        steps=min(_int(max_steps),256)
        if type(ignore_global_phase) is not bool:
            raise ValueError("ignore_global_phase must be bool")
        raw=list(islice(iter(pairs),33))
        if not raw or len(raw)>32:
            raise ValueError("expected 1..32 checkpoint pairs")
        alignment=[]
        for pair in raw:
            values=tuple(islice(iter(pair),3))
            if len(values)!=2:
                raise ValueError("checkpoint pair requires two indices")
            i,j=map(_int,values)
            if i>len(a._qc.data) or j>len(b._qc.data):
                raise ValueError("checkpoint outside circuit")
            if alignment and (i<alignment[-1][0] or j<alignment[-1][1] or (i,j)==alignment[-1]):
                raise ValueError("checkpoint pairs must progress monotonically")
            alignment.append((i,j))
        report={"schema_version":1,"scope":"explicit aligned zero-input checkpoints, not root cause",
                "status":"PASS","checks":[]}
        try:
            if a.num_qubits!=b.num_qubits or a.num_qubits>8 or max(max(p) for p in alignment)>steps:
                raise ResourceLimit("checkpoint widths or step limit unsupported")
            _limit(a.num_qubits,2,budget=budget)
        except ResourceLimit as exc:
            return dict(report,status="UNSUPPORTED",reason=str(exc))
        for i,j in alignment:
            actual=a.debug.checkpoint(i,max_bytes=budget,max_steps=steps)
            expected=b.debug.checkpoint(j,max_bytes=budget,max_steps=steps)
            check=actual.result.test.state(expected.result,ignore_global_phase=ignore_global_phase,atol=tolerance)
            report["checks"].append({"observed_index":i,"reference_index":j,"check":check.to_dict()})
            if check.status=="FAIL":
                report["status"]="FAIL"
                break
        return report
