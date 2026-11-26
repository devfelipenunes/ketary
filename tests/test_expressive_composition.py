"""Native and regression oracles for bounded expressive composition and math."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, SparsePauliOp

def test_repeat_and_placements_strict_operator():
    block=QuantumCircuit(2,global_phase=.19)
    block.h(0)
    block.ry(.35,1)
    block.cx(0,1)
    b=q.from_qiskit(block)
    c=q.Circuit(4).z(3)
    c.register("pair",[3,0])
    c.checkpoint("start")
    native=c.to_qiskit()
    for _ in range(7):
        native.compose(block,qubits=[3,0],inplace=True)
    assert c.apply(b,wires=[3,0],times=7) is c
    for pair in [(1,2),(3,1),(2,0)]:
        native.compose(block,qubits=list(pair),inplace=True)
    assert c.apply_each(b,placements=iter([(1,2),(3,1),(2,0)])) is c
    assert c.to_qiskit()==native
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(native).data,atol=1e-12,rtol=0)
    assert c.checkpoints=={} and c.registers=={"pair":(3,0)}
    assert b.to_qiskit()==block
    repeated=b.repeat(3)
    expected=QuantumCircuit(2)
    for _ in range(3):
        expected.compose(block,inplace=True)
    assert repeated.to_qiskit()==expected
    assert repeated is not b and repeated.registers=={} and repeated.checkpoints=={}
    q.Circuit.from_json(repeated.to_json()).test.equivalent(repeated).require()

def test_large_expansion_and_fixed_self_snapshot():
    layer=q.Circuit(4).apply(q.bell(),wires=[0,1]).h([2,3])
    c=q.Circuit(4).apply(layer,times=1000)
    native=QuantumCircuit(4)
    source=layer.to_qiskit()
    for _ in range(1000):
        native.compose(source,inplace=True)
    assert c.to_qiskit()==native and len(native.data)==4000
    c=q.bell()
    original=c.to_qiskit()
    expected=original.copy()
    for _ in range(3):
        expected.compose(original,inplace=True)
    c.apply(c,times=3)
    assert c.to_qiskit()==expected

@pytest.mark.parametrize("bad",[0,-1,True,1.5])
def test_repeat_rejects_invalid_count(bad):
    c=q.bell()
    before=c.to_json()
    with pytest.raises(ValueError):
        c.apply(q.bell(),times=bad)
    with pytest.raises(ValueError):
        c.repeat(bad)
    assert c.to_json()==before

def test_placement_validation_and_expansion_caps(monkeypatch):
    c=q.Circuit(4).h(0).checkpoint("start")
    block=q.bell()
    before=c.to_json()
    def forbidden(*a,**k):
        pytest.fail("native composition began before preflight")
    monkeypatch.setattr(QuantumCircuit,"compose",forbidden)
    for bad in ([],{(0,1),(2,3)},[(0,1),(0,0)],[(0,1),None],[(0,1),[0,9]]):
        with pytest.raises(ValueError):
            c.apply_each(block,placements=bad)
        assert c.to_json()==before
    with pytest.raises(q.ResourceLimit):
        c.apply(block,wires=[0,1],times=10001)
    with pytest.raises(q.ResourceLimit):
        c.apply_each(block,placements=((0,1) for _ in range(10001)))
    large=q.Circuit(1)
    for _ in range(11):
        large.h(0)
    with pytest.raises(q.ResourceLimit):
        large.repeat(10000)
    assert c.to_json()==before and c.checkpoints=={"start":1}

def test_transaction_rollback_after_later_placement(monkeypatch):
    c=q.Circuit(4).h(0).checkpoint("start")
    native=QuantumCircuit(2,global_phase=.2)
    native.cx(0,1)
    b=q.from_qiskit(native)
    before=c.to_json()
    original=QuantumCircuit.compose
    calls=[]
    def fail_later(self,*a,**kw):
        calls.append(1)
        if len(calls)==2:
            self.x(0)
            self.global_phase=.7
            raise RuntimeError("injected")
        return original(self,*a,**kw)
    monkeypatch.setattr(QuantumCircuit,"compose",fail_later)
    with pytest.raises(RuntimeError):
        c.apply_each(b,placements=[(0,1),(2,3)])
    assert len(calls)==2 and c.to_json()==before and c.checkpoints=={"start":1}

def test_intermediate_phase_invalidation():
    b=q.Circuit(1).to_qiskit()
    b.global_phase=np.pi
    c=q.Circuit(1).checkpoint("start")
    c.apply(q.from_qiskit(b),times=2)
    assert c.checkpoints=={}

def test_grouped_math_native_and_shared_terms(monkeypatch):
    rng=np.random.default_rng(91)
    v=rng.normal(size=8)+1j*rng.normal(size=8)
    v/=np.linalg.norm(v)
    r=q.Result(v)
    H=.3*q.Z(0)+.8*(q.X(0)@q.Y(2))
    terms=[H,"IIZ",{0:"Z"},H]
    native=SparsePauliOp.from_list([("IIZ",.3),("YIX",.8)]).to_matrix()
    z=SparsePauliOp("IIZ").to_matrix()
    expected=[np.vdot(v,native@v).real,np.vdot(v,z@v).real,np.vdot(v,z@v).real,np.vdot(v,native@v).real]
    # Count actual native evaluations rather than a public wrapper call:
    # exactly the same distinct labels, once each, and zero on preflight failure.
    from qiskit.quantum_info import Statevector
    orig=Statevector.expectation_value
    calls=[]
    def tracked(self,operator,*args,**kwargs):
        calls.append(operator.to_label())
        return orig(self,operator,*args,**kwargs)
    monkeypatch.setattr(Statevector,"expectation_value",tracked)
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("implicit execution"))
    np.testing.assert_allclose(r.math.expectations(iter(terms)),expected,atol=1e-12,rtol=0)
    assert calls==["IIZ","YIX"]
    calls.clear()
    for invalid in (["IIZ","BAD"],["IIZ",q.X(4)],["IIZ",{True:"X"}],{"IIZ","YIX"}):
        with pytest.raises(ValueError):
            r.math.expectations(invalid)
    with pytest.raises(q.ResourceLimit):
        r.math.expectations(["IIZ","YIX"],max_work=15)
    with pytest.raises(q.ResourceLimit):
        r.math.expectations(["IIZ"]*33)
    assert calls==[]
