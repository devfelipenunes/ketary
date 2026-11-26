"""Bounded public exception matrix; distinguish invalid, unsupported and resource failures."""
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

@pytest.mark.parametrize("kind,error",[
    ("wrong_block",TypeError),("late_mapping",ValueError),("angle",ValueError),
    ("expansion",q.ResourceLimit),("payload",q.ResourceLimit),
    ("symbolic_run",q.UnsupportedOperation),("classical_unitary",q.UnsupportedOperation),
    ("wrong_native",TypeError),
])
def test_public_boundary(kind,error,monkeypatch):
    c=q.Circuit(2).h(0).checkpoint("prefix").register("pair",[1,0])
    before=c.to_qiskit()
    def forbidden(*a,**k):
        pytest.fail("invalid operation reached native mutation")
    monkeypatch.setattr(QuantumCircuit,"compose",forbidden)
    monkeypatch.setattr(QuantumCircuit,"ry",forbidden)
    if kind=="symbolic_run":
        # Construct using a gate not patched by this test.
        symbolic=q.Circuit.symbolic(1).rx(Parameter("x"),0)
        action=lambda:symbolic.run()
    elif kind=="classical_unitary":
        action=lambda:q.Circuit.classical(1,1).run()
    else:
        action={
            "wrong_block":lambda:c.apply(object()),
            "late_mapping":lambda:c.apply_each(q.Circuit(2),placements=[(0,1),(1,1)]),
            "angle":lambda:c.ry([.2,float("nan")],[0,1]),
            "expansion":lambda:c.apply(q.Circuit(2),times=10001),
            "payload":lambda:c.run(max_bytes=63),
            "wrong_native":lambda:q.from_qiskit(object()),
        }[kind]
    with pytest.raises(error) as info:
        action()
    assert type(info.value) is error
    assert c.to_qiskit()==before
    assert c.checkpoints=={"prefix":1} and c.registers=={"pair":(1,0)}

def test_optional_dependency_and_preflight(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules,"qiskit_aer",None)
    c=q.Circuit.classical(1,1).measure(0,0)
    before=c.to_qiskit()
    with pytest.raises(q.UnsupportedOperation,match="dynamic"):
        c.run_shots(shots=8)
    with pytest.raises(q.ResourceLimit):
        c.run_shots(shots=10001)
    with pytest.raises(ValueError):
        c.run_shots(seed=2**32)
    assert c.to_qiskit()==before
