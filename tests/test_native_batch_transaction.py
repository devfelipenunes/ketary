"""Native batch fast path: exact sequence, strict operator and rollback."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator


@pytest.mark.parametrize("name,params",[
    ("h",()),("x",()),("y",()),("z",()),("s",()),("sdg",()),("t",()),("tdg",()),
    ("sx",()),("sxdg",()),("rx",(.32,)),("ry",(.41,)),("rz",(-.22,)),
    ("p",(.8,)),("u",(.1,.2,.3)),
])
def test_native_broadcast_sequence_and_phase(name,params):
    native=QuantumCircuit(4,global_phase=.37)
    native.h(1)
    c=q.from_qiskit(native).checkpoint("prefix")
    c.register("data",[3,0,2])
    for w in [3,0,2]:
        getattr(native,name)(*params,w)
    assert getattr(c,name)(*params,iter([3,0,2])) is c
    assert c.to_qiskit()==native
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(native).data,atol=1e-12,rtol=0)
    assert c.checkpoints=={"prefix":1} and c.registers=={"data":(3,0,2)}


def test_bound_batch_no_prefix_or_staging_copy(monkeypatch):
    c=q.Circuit(4).h(0)
    def forbidden(*a,**kw):
        pytest.fail("bound batch must not allocate or compose a staging circuit")
    monkeypatch.setattr(QuantumCircuit,"copy",forbidden)
    monkeypatch.setattr(QuantumCircuit,"compose",forbidden)
    monkeypatch.setattr(QuantumCircuit,"__init__",forbidden)
    c.h([2,3]).ry([.1,.2],[3,1]).u(.2,.3,.4,[0,2])
    assert len(c._qc.data)==7


@pytest.mark.parametrize("name,call",[
    ("h",lambda c:c.h([2,0,1])),
    ("ry",lambda c:c.ry([.1,.2,.3],[2,0,1])),
])
def test_native_partial_append_rollback(name,call,monkeypatch):
    native=QuantumCircuit(3,global_phase=.13)
    native.x(1)
    c=q.from_qiskit(native).checkpoint("prefix")
    before=c.to_json()
    original=getattr(QuantumCircuit,name)
    def fail(self,*a,**kw):
        original(self,*a,**kw)
        self.global_phase=.8
        raise RuntimeError("injected after append")
    monkeypatch.setattr(QuantumCircuit,name,fail)
    with pytest.raises(RuntimeError):
        call(c)
    assert c.to_json()==before and c.checkpoints=={"prefix":1}


def test_invalid_angles_fail_before_native_append(monkeypatch):
    c=q.Circuit(3).x(0)
    before=c.to_json()
    def forbidden(*a,**kw):
        pytest.fail("native append before preflight")
    monkeypatch.setattr(QuantumCircuit,"ry",forbidden)
    monkeypatch.setattr(QuantumCircuit,"u",forbidden)
    for call in (lambda:c.ry([.1,float("nan")],[0,1]),
                 lambda:c.u(.2,float("inf"),.3,[0,2]),
                 lambda:c.ry([.1,.2],[0,0])):
        with pytest.raises(ValueError):
            call()
        assert c.to_json()==before


def test_symbolic_name_collision_keeps_original_parameter_table():
    from qiskit.circuit import Parameter
    a,b=Parameter("theta"),Parameter("theta")
    c=q.Circuit.symbolic(3).ry(a,0)
    before=c.to_qiskit()
    with pytest.raises(Exception,match="name conflict|name.*already|parameter"):
        c.ry([a,b],[1,2])
    assert c.to_qiskit()==before and c.parameters==(a,)


def test_classical_batch_preserves_measurement_order():
    c=q.Circuit.classical(3,3).h([2,0]).measure([2,0],[0,2]).ry([.3,.7],[0,2])
    native=QuantumCircuit(3,3)
    native.h([2,0])
    native.measure([2,0],[0,2])
    native.ry(.3,0)
    native.ry(.7,2)
    assert c.to_qiskit()==native
