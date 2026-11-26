"""Independent terminal deletion checks and fixed-reference execution count."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

def artifact(a,b,label="0",ignore=False):
    r=a.test.compare(b,inputs=[label],ignore_global_phase=ignore)
    assert r["status"]=="FAIL" and r["evidence"] is not None
    return q.Evidence.from_dict(r["evidence"])

def test_restart_revisits_previously_rejected_deletion(monkeypatch):
    a=q.Circuit(1).x(0).h(0)
    b=q.Circuit(1).h(0)
    e=artifact(a,b)
    original=q.Circuit.run
    calls=[]
    def counted(self,*args,**kw):
        calls.append(len(self.to_qiskit().data))
        return original(self,*args,**kw)
    monkeypatch.setattr(q.Circuit,"run",counted)
    reduced=e.minimize(max_attempts=3)
    assert reduced["status"]=="FAIL"
    assert reduced["before_gates"]==2 and reduced["after_gates"]==0
    assert reduced["attempts"]==3 and not reduced["budget_exhausted"]
    assert len(calls)==5
    assert q.Evidence.from_dict(reduced["evidence"]).reproduce()["reproduced"]
    assert a.inspect()["gate_count"]==2 and b.inspect()["gate_count"]==1

def test_budget_retains_reproducible_witness_without_minimality_claim():
    e=artifact(q.Circuit(1).x(0).h(0),q.Circuit(1).h(0))
    reduced=e.minimize(max_attempts=2)
    assert reduced["after_gates"]==1 and reduced["budget_exhausted"]
    assert reduced["attempts"]==2
    assert q.Evidence.from_dict(reduced["evidence"]).reproduce()["reproduced"]

@pytest.mark.parametrize("seed",range(16))
@pytest.mark.parametrize("ignore",[False,True])
def test_completed_scan_is_one_deletion_local_minimum(seed,ignore):
    rng=np.random.default_rng(7400+seed)
    a=QuantumCircuit(2)
    for i in range(7):
        gate=str(rng.choice(["h","x","z","s"]))
        getattr(a,gate)(int(rng.integers(2)))
    b=QuantumCircuit(2);b.ry(.37,0);b.cx(0,1)
    label="0+"
    e=artifact(q.from_qiskit(a),q.from_qiskit(b),label,ignore)
    reduced=e.minimize(max_attempts=128)
    assert not reduced["budget_exhausted"]
    assert reduced["attempts"]<=128
    data=reduced["evidence"]["data"]
    observed=q.Circuit.from_json(data["observed"]).to_qiskit()
    ref=Statevector.from_label(label).evolve(b).data
    def distance(c):
        v=Statevector.from_label(label).evolve(c).data
        overlap=np.vdot(ref,v)
        if ignore and abs(overlap)>0:
            v=v*np.conj(overlap)/abs(overlap)
        return np.linalg.norm(v-ref)
    assert distance(observed)>data["atol"]
    for i in range(len(observed.data)):
        trial=observed.copy();del trial.data[i]
        assert distance(trial)<=data["atol"]
    assert q.Evidence.from_dict(reduced["evidence"]).reproduce()["reproduced"]
