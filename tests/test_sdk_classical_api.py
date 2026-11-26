import sys
import pytest
import ketary as q


def test_classical_builder_and_unitary_guards(monkeypatch):
    c=q.Circuit.classical(2,2).h(0).measure(0,0).if_x(1,0).measure(1,1)
    assert c.num_clbits==2
    assert [x.operation.name for x in c.to_qiskit().data]==["h","measure","if_else","measure"]
    d=c.copy().reset(1)
    assert len(d.to_qiskit().data)==5 and len(c.to_qiskit().data)==4
    for operation in (c.run,c.inspect,c.to_json,c.inverse,c.optimize,c.decompose,
                      lambda:c.transpile(basis_gates=["u","cx"]),c.debug.trace,
                      lambda:c.debug.checkpoint(0),lambda:c.debug.compare(c),
                      lambda:c.test.equivalent(c),lambda:c.compose(c),
                      lambda:c.bind({})):
        with pytest.raises(q.UnsupportedOperation):
            operation()
    monkeypatch.setitem(sys.modules,"qiskit_aer",None)
    with pytest.raises(q.UnsupportedOperation,match="dynamic"):
        c.run_shots(shots=1,seed=0)


def test_classical_validation_and_atomicity():
    with pytest.raises(q.ResourceLimit):
        q.Circuit.classical(13,1)
    c=q.Circuit.classical(2,1)
    for operation in (lambda:c.measure(0,1),lambda:c.if_x(0,0,value=2),lambda:c.reset(2)):
        with pytest.raises(ValueError):
            operation()
    assert not c.to_qiskit().data
    with pytest.raises(ValueError):
        c.run_shots()
    with pytest.raises(q.UnsupportedOperation):
        q.Circuit(1).measure(0,0)
    with pytest.raises(q.UnsupportedOperation):
        q.Circuit(1).reset(0)
    with pytest.raises(q.UnsupportedOperation):
        q.bell().run_shots()
    c.measure(0,0)
    for kwargs in ({"shots":10001},{"max_bytes":1}):
        with pytest.raises(q.ResourceLimit):
            c.run_shots(**kwargs)
    with pytest.raises(ValueError):
        c.run_shots(seed=2**32)
    with pytest.raises(q.UnsupportedOperation):
        q.from_qiskit(c.to_qiskit())
    assert q.teleportation(.2,.4,verify=True).num_clbits==3
    with pytest.raises(ValueError):
        q.teleportation(0,0,verify=1)
