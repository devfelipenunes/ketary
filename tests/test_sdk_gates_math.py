import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

@pytest.mark.parametrize("gate,args",[["p",[0.37,0]],["u",[0.2,-0.4,0.7,0]],["cp",[0.37,0,1]],["ch",[0,1]],["crx",[0.37,0,1]],["cry",[0.37,0,1]],["crz",[0.37,0,1]],["sx",[0]],["sxdg",[0]],["cy",[0,1]],["cswap",[0,1,2]],["rxx",[0.37,0,1]],["ryy",[0.37,0,1]],["rzz",[0.37,0,1]]])
def test_extended_gate_operator_replay_inverse(gate,args):
    c=q.Circuit(3)
    native=QuantumCircuit(3)
    getattr(native,gate)(*args)
    getattr(c,gate)(*args)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(native).data,atol=1e-12,rtol=0)
    c.test.equivalent(q.Circuit.from_json(c.to_json())).require()
    c.compose(c.inverse()).test.equivalent(q.Circuit(3)).require()

def test_reduced_density_purity_and_observable():
    r=q.bell().run()
    np.testing.assert_allclose(r.math.density_matrix([0]),np.eye(2)/2,atol=1e-12)
    assert r.math.purity([1])==pytest.approx(.5)
    assert r.math.purity()==1
    assert r.math.observable({"XX":.5,"ZZ":.5})==pytest.approx(1)
    assert "|00>" in r.math.dirac() and "|11>" in r.math.dirac()
    with pytest.raises(q.ResourceLimit):
        r.math.density_matrix(max_bytes=64)

def test_density_wire_order():
    r=q.Circuit(3).x(0).run()
    np.testing.assert_allclose(r.math.density_matrix([0,2]),np.diag([0,0,1,0]))
    np.testing.assert_allclose(r.math.density_matrix([2,0]),np.diag([0,1,0,0]))

def test_incremental_comparison_no_materialized_trace(monkeypatch):
    c=q.bell().z(0)
    r=q.bell().x(0)
    monkeypatch.setattr(type(c.debug),"trace",lambda *a,**k:pytest.fail("materialized trace"))
    assert c.debug.compare(r).step_index==3
