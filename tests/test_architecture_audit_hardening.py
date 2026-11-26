"""Audit regressions: bound append path, rollback, ownership and legacy order."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

def test_repeated_batches_do_not_copy_prefix(monkeypatch):
    c=q.Circuit(4)
    c.register("pair",[3,0])
    c.checkpoint("initial")
    native=QuantumCircuit(4)
    def forbidden(*a,**k):
        pytest.fail("bound batch copied full Circuit")
    monkeypatch.setattr(q.Circuit,"copy",forbidden)
    for _ in range(100):
        c.ry(.23,[3,0])
        native.ry(.23,[3,0])
    assert c.to_qiskit()==native
    assert c.checkpoints=={"initial":0} and c.registers=={"pair":(3,0)}
    before=c.to_json()
    with pytest.raises(ValueError):
        c.ry(float("nan"),[3,0])
    assert c.to_json()==before

def test_apply_inplace_without_facade_copy_and_self_application(monkeypatch):
    c=q.Circuit(3).h(2)
    native=QuantumCircuit(2,global_phase=.31)
    native.h(0); native.cx(0,1)
    block=q.from_qiskit(native)
    expected=c.to_qiskit()
    expected.compose(native,qubits=[2,0],inplace=True)
    c.checkpoint("before")
    def forbidden(*a,**k):
        pytest.fail("apply used copy-returning facade composition")
    monkeypatch.setattr(q.Circuit,"compose",forbidden)
    c.apply(block,wires=[2,0])
    assert c.checkpoints=={}
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(expected).data,atol=1e-12,rtol=0)
    expected=expected.compose(expected)
    c.apply(c)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(expected).data,atol=1e-12,rtol=0)

def test_native_append_rollback_on_partial_failure(monkeypatch):
    c=q.bell().checkpoint("ready")
    before=c.to_json()
    block=q.bell()
    def fail(self,*a,**k):
        self.x(0)
        self.global_phase=.73
        raise RuntimeError("injected native failure")
    monkeypatch.setattr(QuantumCircuit,"compose",fail)
    with pytest.raises(RuntimeError):
        c.apply(block)
    assert c.to_json()==before and c.checkpoints=={"ready":2}
    with pytest.raises(RuntimeError):
        c.h([0,1])
    assert c.to_json()==before

def test_symbolic_and_classical_batch_preserve_existing_paths():
    p=q.Circuit.parameter("theta")
    c=q.Circuit.symbolic(2).ry(p,[1,0])
    expected=q.Circuit(2).ry(.3,1).ry(.3,0)
    c.bind(theta=.3).test.equivalent(expected).require()
    d=q.Circuit.classical(2,2).h([1,0]).measure(0,0).measure(1,1)
    assert d.num_clbits==2 and len(d.to_qiskit().data)==4

def test_legacy_order_compatibility_and_explicit_order():
    r=q.Circuit(3).x(2).run()
    assert r.math.marginal_probabilities([2,0])["10"]==pytest.approx(1)
    assert r.math.marginal_probabilities(iter([0,2]))["01"]==pytest.approx(1)
    # Historical iterable acceptance stays intact; order of sets is not promised.
    assert sum(r.math.marginal_probabilities({0,2}).values())==pytest.approx(1)
    c=q.Circuit(2).h_many({0,1})
    c.test.equivalent(q.Circuit(2).h([0,1])).require()
    with pytest.raises(ValueError):
        q.Circuit(2).h({0,1})
