import numpy as np
import pytest
import ketary as q

def test_snapshot_copy_budget():
    r=q.bell().run()
    with pytest.raises(q.ResourceLimit): r.math.statevector(max_bytes=63)
    assert r.math.statevector(max_bytes=64).size==4

def test_svd_limits_before_allocation(monkeypatch):
    r=q.ghz(4).run()
    def fail(*args,**kwargs): raise AssertionError("SVD must not run")
    monkeypatch.setattr(np.linalg,"svd",fail)
    with pytest.raises(q.ResourceLimit): r.math.entropy(([0,1],[2,3]),max_rank=3)
    with pytest.raises(q.ResourceLimit): r.test.entangled(partition=([0,1],[2,3]),max_bytes=255)

def test_svd_limits_exact():
    r=q.bell().run()
    assert r.math.entropy(([0],[1]),max_rank=2,max_bytes=64)==pytest.approx(1)

def test_drawing_limits():
    c=q.bell()
    with pytest.raises(q.ResourceLimit): c.visualize.text(max_qubits=1)
    with pytest.raises(q.ResourceLimit): c.visualize.text(max_gates=1)
    assert "H" in c.visualize.text(max_qubits=2,max_gates=2)

def test_shots_limit():
    with pytest.raises(q.ResourceLimit): q.bell().run().sample(shots=2**63)
