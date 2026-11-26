"""Explicit checks of quantum states and complete small operators."""
from __future__ import annotations
import numpy as np
from ._validation import _int, _tol
from ._result import CheckResult

def _residual(actual,expected,ignore_global_phase,atol):
    t=_tol(atol)
    if type(ignore_global_phase) is not bool:
        raise ValueError("ignore_global_phase must be bool")
    if actual.shape!=expected.shape:
        raise ValueError("dimension mismatch")
    if ignore_global_phase:
        overlap=np.vdot(expected,actual)
        if abs(overlap)>0:
            actual=actual*(np.conj(overlap)/abs(overlap))
    error=float(np.max(np.abs(actual-expected)))
    return CheckResult("PASS" if error<=t else "FAIL",error,0,t,
                       "max absolute residual; phase "+("ignored" if ignore_global_phase else "preserved"))

class _CircuitChecks:
    def __init__(self,circuit):
        self._c=circuit

    def equivalent(self,other,*,ignore_global_phase=False,atol=1e-9,max_bytes=16*1024**2):
        """Compare complete operators (not just their action on |0...0>).

        Strict phase comparison by default. Ignoring phase is only appropriate
        for standalone unitary equivalence, not arbitrary controlled contexts.
        The byte budget counts the two dense complex128 matrix payloads only.
        """
        from ._circuit import Circuit
        t=_tol(atol)
        budget=_int(max_bytes,1)
        if type(ignore_global_phase) is not bool:
            raise ValueError("ignore_global_phase must be bool")
        if not isinstance(other,Circuit):
            raise TypeError("expected Circuit")
        self._c._require_bound()
        other._require_bound()
        n=self._c.num_qubits
        if n!=other.num_qubits:
            return CheckResult("FAIL",None,None,t,"different qubit counts")
        if n>8 or 32*(1<<(2*n))>budget:
            return CheckResult("UNSUPPORTED",None,None,t,"operator payload or eight-qubit limit exceeded")
        from qiskit.quantum_info import Operator
        return _residual(Operator(self._c._qc).data,Operator(other._qc).data,ignore_global_phase,t)


    def metrics(self,other,*,ignore_global_phase=False,atol=1e-9,max_bytes=16*1024**2):
        """Dense numerical metrics, not formal proof; common aligned phase."""
        from ._circuit import Circuit
        from qiskit.quantum_info import Operator
        if not isinstance(other,Circuit):
            raise TypeError("expected Circuit")
        self._c._require_bound()
        other._require_bound()
        t=_tol(atol)
        budget=_int(max_bytes,1)
        if type(ignore_global_phase) is not bool:
            raise ValueError("ignore_global_phase must be bool")
        n=self._c.num_qubits
        report={"schema_version":1,"scope":"complete ideal unitary matrices; numerical tolerance",
                "phase_policy":"overlap alignment" if ignore_global_phase else "strict",
                "atol":t}
        if n!=other.num_qubits:
            return dict(report,status="FAIL",reason="width mismatch")
        if n>8 or 48*(1<<(2*n))>budget:
            return dict(report,status="UNSUPPORTED",reason="three matrix payload budget or width exceeded")
        a,b=Operator(self._c._qc).data,Operator(other._qc).data
        overlap=np.vdot(b,a)
        fidelity=float(np.clip(abs(overlap)**2/(a.shape[0]**2),0,1))
        if ignore_global_phase and abs(overlap)>0:
            a=a*(np.conj(overlap)/abs(overlap))
        delta=a-b
        spectral=float(np.linalg.norm(delta,ord=2))
        return dict(report,status="PASS" if spectral<=t else "FAIL",
                    max_element_error=float(np.max(np.abs(delta))),
                    frobenius_norm=float(np.linalg.norm(delta)),
                    operator_norm=spectral,process_fidelity=fidelity)


    def compare(self,other,*,inputs=None,complete=True,ignore_global_phase=False,atol=1e-9,max_bytes=64*1024**2):
        from ._verification import compare
        return compare(self._c,other,inputs=inputs,complete=complete,ignore_global_phase=ignore_global_phase,
                       atol=atol,max_bytes=max_bytes)

    def external_equivalence(self,other,*,deadline=10):
        from ._external import qcec_compare
        return qcec_compare(self._c,other,deadline=deadline)
