import itertools
import numpy as np
import pytest
import ketary as q
from qiskit.circuit.library import XGate
from qiskit.quantum_info import SparsePauliOp


def test_bounded_iterables_atomic():
    c=q.bell()
    before=c.to_json()
    with pytest.raises(ValueError):
        c.append(XGate(),itertools.repeat(0))
    with pytest.raises(ValueError):
        c.compose(q.Circuit(1),wires=itertools.repeat(0))
    assert c.to_json()==before
    assert c.compose(q.Circuit(1).x(0),wires=iter([1])).inspect()["gate_count"]==3


def test_initial_shape_preflight(monkeypatch):
    import ketary._execution as module
    class UnexpectedResult:
        def __init__(self,*args):
            pytest.fail("invalid dimension reached Result constructor")
    monkeypatch.setattr(module,"Result",UnexpectedResult)
    for value in ([1,0],np.zeros((4,1)),np.zeros(8)):
        with pytest.raises(ValueError):
            q.Circuit(2).run(initial_state=value)


def test_observable_variance_against_dense_oracle():
    r=q.Circuit(2).ry(.3,0).cx(0,1).rz(.7,1).run()
    terms={"XX":.7,"ZI":-.2,"IZ":.4,"II":2}
    state=r.math.statevector()
    m=SparsePauliOp.from_list(list(terms.items())).to_matrix()
    expected=np.vdot(state,m@m@state).real-np.vdot(state,m@state).real**2
    assert r.math.observable_variance(terms)==pytest.approx(expected,abs=1e-12)
    assert q.bell().run().math.observable_variance({"XX":.5,"ZZ":.5})==pytest.approx(0,abs=1e-12)
    assert q.Circuit(1).run().math.observable_variance({"X":1,"Z":1})==pytest.approx(1)
    for invalid in ({},[],{"X":1},{"XX":True},{"ZZ":float("nan")}):
        with pytest.raises(ValueError):
            r.math.observable_variance(invalid)
    with pytest.raises(q.ResourceLimit):
        r.math.observable_variance(terms,max_bytes=255)
    with pytest.raises(q.ResourceLimit):
        q.Circuit(9).run().math.observable_variance({"I"*9:1})
