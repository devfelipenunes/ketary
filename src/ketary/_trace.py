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
        cursor=_Cursor(self._c)
        return tuple(cursor.at(i) for i in range(len(qc.data)+1))

    def checkpoint(self,index,*,max_bytes=64*1024**2,max_steps=256):
        """Explicit zero-input evolution through one requested checkpoint."""
        self._c._require_bound()
        qc=self._c._qc
        index=self._c._checkpoint_index(index)
        if index>len(qc.data):
            raise ValueError("checkpoint outside circuit")
        if qc.num_qubits>8 or index>_int(max_steps):
            raise ResourceLimit("checkpoint limit exceeded")
        _limit(qc.num_qubits,budget=max_bytes)
        return _Cursor(self._c).at(index)

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
            cursor=_Cursor(c)
            for index in range(len(c._qc.data)+1):
                yield cursor.at(index)
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
        from ._reports import DiagnosticReport
        return DiagnosticReport(self._compare_checkpoints(reference,pairs,ignore_global_phase=ignore_global_phase,atol=atol,max_bytes=max_bytes,max_steps=max_steps))

    def _compare_checkpoints(self,reference,pairs,*,ignore_global_phase=True,atol=1e-9,
                            max_bytes=64*1024**2,max_steps=256):
        """Compare explicitly supplied (observed, reference) checkpoint indices.

        Different circuit lengths are allowed. Alignment is caller-provided,
        not inferred. At most 32 strictly increasing index pairs; an index
        may repeat on one side. Each cursor advances monotonically; previous gates are not replayed.
        """
        from itertools import islice
        from collections.abc import Mapping
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
            if isinstance(pair,(str,bytes,set,frozenset,Mapping)):
                raise ValueError("expected an ordered pair of checkpoint indices or names")
            values=tuple(islice(iter(pair),3))
            if len(values)!=2:
                raise ValueError("checkpoint pair requires two indices")
            i,j=a._checkpoint_index(values[0]),b._checkpoint_index(values[1])
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
        left=_Cursor(a)
        right=_Cursor(b)
        for i,j in alignment:
            actual=left.at(i)
            expected=right.at(j)
            check=actual.result.test.state(expected.result,ignore_global_phase=ignore_global_phase,atol=tolerance)
            report["checks"].append({"observed_index":i,"reference_index":j,"check":check.to_dict()})
            if check.status=="FAIL":
                report["status"]="FAIL"
                break
        return report


    def verify_checkpoints(self,contracts,*,max_bytes=64*1024**2,max_steps=256):
        from ._reports import DiagnosticReport
        return DiagnosticReport(self._verify_checkpoints(contracts,max_bytes=max_bytes,max_steps=max_steps))

    def _verify_checkpoints(self,contracts,*,max_bytes=64*1024**2,max_steps=256):
        """Verify named-by-index contracts on the zero-input trajectory."""
        from collections.abc import Mapping
        from ._contracts import Contract
        self._c._require_bound()
        if not isinstance(contracts,Mapping) or not 1<=len(contracts)<=32:
            raise ValueError("expected 1..32 checkpoint contracts")
        qc=self._c._qc
        if qc.num_qubits>8:
            raise ResourceLimit("checkpoint width exceeds eight")
        _limit(qc.num_qubits,2,budget=max_bytes)
        steps=min(_int(max_steps),256)
        requested=[]
        for index,contract in contracts.items():
            index=self._c._checkpoint_index(index)
            if index>len(qc.data):
                raise ValueError("checkpoint outside circuit")
            if index>steps:
                raise ResourceLimit("checkpoint step limit exceeded")
            if not isinstance(contract,Contract) or contract.num_qubits!=qc.num_qubits:
                raise ValueError("expected width-matched Contract")
            requested.append((index,contract))
        if len({index for index,_ in requested})!=len(requested):
            raise ValueError("duplicate resolved checkpoints")
        cursor=_Cursor(self._c)
        rows=[]
        for index,contract in sorted(requested):
            step=cursor.at(index)
            report=contract.verify(step.result)
            rows.append({"index":index,"operation":step.operation,"wires":list(step.wires),
                         "contract":contract.to_dict(),"report":report.to_dict()})
            if report.status!="PASS":
                return {"schema_version":1,"status":report.status,"scope":"zero-input requested checkpoints",
                        "first_nonpass":index,"checks":rows}
        return {"schema_version":1,"status":"PASS","scope":"zero-input requested checkpoints",
                "first_nonpass":None,"checks":rows}


class _Cursor:
    """Private, call-local monotonic native state evolution."""
    def __init__(self,c):
        self.qc=c._qc
        _,SV=_sdk()
        a=np.zeros(1<<c.num_qubits,dtype=complex)
        a[0]=np.exp(1j*float(self.qc.global_phase))
        self.state=SV(a)
        self.index=0
        self.operation="initial (global phase applied)"
        self.wires=()

    def at(self,index):
        while self.index<index:
            item=self.qc.data[self.index]
            self.wires=tuple(self.qc.find_bit(w).index for w in item.qubits)
            self.operation=item.operation.name
            self.state=self.state.evolve(item.operation,qargs=list(self.wires))
            self.index+=1
        return TraceStep(self.operation,self.wires,Result(self.state.data))
