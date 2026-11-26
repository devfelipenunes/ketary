import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator


def test_symbolic_lifecycle():
    a=q.Circuit.parameter("a")
    b=q.Circuit.parameter("b")
    t=q.Circuit.symbolic(2).ry(a,0).cp(2*b,0,1).u(a,b,-a,1)
    assert set(t.parameters)=={a,b}
    copied=t.copy().rz(a,0)
    assert len(copied.to_qiskit().data)==4 and len(t.to_qiskit().data)==3
    bound=t.bind({a:.2,b:.3})
    expected=q.Circuit(2).ry(.2,0).cp(.6,0,1).u(.2,.3,-.2,1)
    bound.test.equivalent(expected).require()
    assert not bound.parameters and set(t.parameters)=={a,b}
    assert bound.run().test.normalized().status=="PASS"
    for bindings in ({a:.2},{a:.2,b:True},{a:.2,b:.3,q.Circuit.parameter("extra"):0}):
        with pytest.raises(ValueError):
            t.bind(bindings)
    for operation in (t.run,t.inspect,t.to_json,t.inverse,t.optimize,t.decompose,
                      lambda:t.transpile(basis_gates=["u","cx"]),t.debug.trace,
                      lambda:t.debug.checkpoint(0),lambda:t.debug.compare(t),
                      lambda:t.test.equivalent(t),lambda:t.compose(t)):
        with pytest.raises(q.UnsupportedOperation):
            operation()


def test_default_mode_remains_strict():
    a=q.Circuit.parameter("a")
    with pytest.raises(ValueError):
        q.Circuit(1).rx(a,0)
    for name in ("", "x"*129, 3):
        with pytest.raises(ValueError):
            q.Circuit.parameter(name)
    c=q.Circuit.symbolic(1).rz(a,0)
    with pytest.raises(q.UnsupportedOperation):
        q.from_qiskit(c.to_qiskit())
