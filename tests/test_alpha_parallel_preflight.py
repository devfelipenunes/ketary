"""Independent negative controls for existing bounded contracts."""
import json
import numpy as np
import pytest
import ketary as q
from ketary import _execution,_replay
from qiskit.quantum_info import Operator

@pytest.mark.parametrize("kind",["invalid_late","budget","unbounded"])
def test_run_many_rejects_before_native_evolution(kind,monkeypatch):
    c=q.bell()
    def fail(*args,**kwargs):pytest.fail("native evolution before complete admission")
    monkeypatch.setattr(_execution,"execute_ideal",fail)
    if kind=="invalid_late":
        with pytest.raises(ValueError):c.run_many(["00",np.zeros(4)])
    elif kind=="budget":
        with pytest.raises(q.ResourceLimit):c.run_many(["00","11"],max_bytes=319)
    else:
        consumed=[]
        def infinite():
            while True:
                consumed.append(1);yield "00"
        with pytest.raises(q.ResourceLimit):c.run_many(infinite())
        assert len(consumed)==33

@pytest.mark.parametrize("kind",["view","readonly","borrowed","fresh"])
def test_native_snapshot_admission(kind):
    base=np.array([1,0,0,0],dtype=np.complex128)
    borrowed=None
    if kind=="view":a=base.reshape(2,2).ravel()
    elif kind=="readonly":a=base.copy();a.flags.writeable=False
    elif kind=="borrowed":a=base;borrowed=base
    else:a=base.copy()
    r=q.Result._from_evolution(a,borrowed=borrowed)
    assert not r._data.flags.writeable
    if kind!="fresh":assert not np.shares_memory(r._data,a)
    exported=r.math.statevector();exported[:]=0
    np.testing.assert_array_equal(r.math.statevector(),base)

@pytest.mark.parametrize("kind",["duplicate","overflow","bad_wire","bad_version","surrogate","deep"])
def test_replay_rejects_before_circuit_allocation(kind,monkeypatch):
    payload=q.bell().to_json();data=json.loads(payload)
    if kind=="duplicate":payload=payload.replace('"schema_version":1','"schema_version":1,"schema_version":1')
    elif kind=="overflow":payload=payload.replace('"global_phase":0.0','"global_phase":1e999')
    elif kind=="bad_wire":data["operations"][-1]["wires"]=[0,0];payload=json.dumps(data)
    elif kind=="bad_version":data["schema_version"]=True;payload=json.dumps(data)
    elif kind=="surrogate":payload="\ud800"
    else:payload="["*2000+"0"+"]"*2000
    def fail(*args,**kwargs):pytest.fail("native allocation before complete replay admission")
    monkeypatch.setattr(_replay,"_sdk",fail)
    with pytest.raises(ValueError):q.Circuit.from_json(payload)

@pytest.mark.parametrize("mutation",["phase","control","wire"])
def test_scope_calibration(mutation):
    ref=q.Circuit(3).h(0).cx(0,2)
    if mutation=="phase":bad=ref.copy().z(2)
    elif mutation=="control":bad=q.Circuit(3).h(0).cx(1,2)
    else:bad=q.Circuit(3).h(0).cx(0,1)
    a,b=Operator(ref.to_qiskit()).data,Operator(bad.to_qiskit()).data
    assert np.max(abs(a-b))>1e-9
    assert ref.test.compare(bad,complete=True).status=="FAIL"
    if mutation=="phase":
        np.testing.assert_allclose(list(ref.run().math.probabilities().values()),list(bad.run().math.probabilities().values()),atol=1e-9,rtol=0)
    r=ref.test.compare(bad,inputs=["000"],complete=False)
    assert r.status in ("INCONCLUSIVE","FAIL")
    if r.evidence is not None:assert r.evidence.reproduce()["reproduced"]

def test_replay_roundtrip_strict_phase_and_independent_copy():
    raw=q.Circuit(3).ry(.37,2).cx(2,0).evolve(q.I(),time=.41)
    copy=q.Circuit.from_json(raw.to_json())
    before=copy.to_qiskit()
    raw.x(1)
    assert copy.to_qiskit()==before
    assert copy.test.compare(raw,complete=True).status=="FAIL"
