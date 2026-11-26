"""Explicit optional QCEC experiment; no automatic guarantee promotion."""
from ._validation import _real,ResourceLimit

def qcec_compare(a,b,*,deadline=10):
    from ._circuit import Circuit
    if not isinstance(a,Circuit) or not isinstance(b,Circuit):
        raise TypeError("expected Circuit")
    a._require_bound()
    b._require_bound()
    limit=_real(deadline)
    if not 0<limit<=60:
        raise ValueError("deadline must be in (0,60] seconds")
    if a.num_qubits!=b.num_qubits or a.num_qubits>22 or max(len(a._qc.data),len(b._qc.data))>256:
        raise ResourceLimit("QCEC experiment requires matching widths <=22 and <=256 gates")
    report={"schema_version":1,"scope":"external QCEC native equivalence relation; not Ketary strict phase/metric guarantee"}
    try:
        from mqt import qcec
    except ImportError:
        return dict(report,status="UNSUPPORTED",reason="optional mqt.qcec dependency missing")
    from importlib.metadata import version
    report["backend_version"]=version("mqt.qcec")
    try:
        result=qcec.verify_with_hard_timeout(a.to_qiskit(),b.to_qiskit(),deadline=limit)
    except TimeoutError:
        return dict(report,status="INCONCLUSIVE",reason="external worker deadline exceeded")
    except (RuntimeError,ValueError,TypeError) as exc:
        return dict(report,status="UNSUPPORTED",reason=type(exc).__name__)
    # Preserve the external status verbatim; only explicitly definitive
    # up-to-global-phase criteria are promoted, never probable equivalence.
    raw=result.get("equivalence")
    status="PASS" if raw in ("equivalent","equivalent_up_to_global_phase") else "FAIL" if raw=="not_equivalent" else "INCONCLUSIVE"
    return dict(report,status=status,external_equivalence=str(raw))
