import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator

@pytest.mark.parametrize("phase_policy",[False,True])
@pytest.mark.parametrize("delta",[0.,1e-12,.17])
def test_complete_metrics_against_original_svd(delta,phase_policy):
    a=q.Circuit(3).h(0).cx(0,2).ry(.31,1)
    b=a.copy()
    if delta:b.rz(delta,2)
    A=Operator(a.to_qiskit()).data;B=Operator(b.to_qiskit()).data
    overlap=np.vdot(B,A)
    fidelity=float(np.clip(abs(overlap)**2/A.shape[0]**2,0,1))
    if phase_policy and abs(overlap)>0:A=A*(np.conj(overlap)/abs(overlap))
    d=A-B
    expected=(float(np.max(np.abs(d))),float(np.linalg.norm(d)),float(np.linalg.norm(d,ord=2)),fidelity)
    report=a.test.metrics(b,ignore_global_phase=phase_policy)
    assert tuple(report[k] for k in ("max_element_error","frobenius_norm","operator_norm","process_fidelity"))==expected
    assert report["status"]==("PASS" if expected[2]<=1e-9 else "FAIL")

def test_zero_residual_skips_svd_not_operator_evaluation(monkeypatch):
    a=q.Circuit(3).h(0).cx(0,2)
    b=a.copy()
    real=np.linalg.norm
    calls=[]
    def spy(x,*args,**kwargs):
        if kwargs.get("ord")==2:calls.append(x.shape)
        return real(x,*args,**kwargs)
    monkeypatch.setattr(np.linalg,"norm",spy)
    assert a.test.metrics(b)["operator_norm"]==0
    assert not calls
    b.x(1)
    assert a.test.metrics(b)["status"]=="FAIL"
    assert calls==[(8,8)]

def test_zero_residual_still_checks_width_and_budget():
    a=q.Circuit(4)
    assert a.test.metrics(a,max_bytes=1)["status"]=="UNSUPPORTED"
    assert a.test.metrics(q.Circuit(3))["status"]=="FAIL"
