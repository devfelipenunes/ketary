import itertools
import math
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import SparsePauliOp

def test_expression_exact_wire_order():
    h=.5*q.Z(0)+.3*q.Z(2)+.8*(q.X(0)@q.Y(2))
    assert h.num_qubits==3
    assert h.to_dict()=={"IIZ":.5,"YIX":.8,"ZII":.3}
    assert h.to_dict(4)=={"IIIZ":.5,"IYIX":.8,"IZII":.3}
    expected=SparsePauliOp.from_list([("IIZ",.5),("YIX",.8),("ZII",.3)])
    np.testing.assert_allclose(h.to_qiskit().to_matrix(),expected.to_matrix())
    with pytest.raises(ValueError):
        h.to_dict(2)
    copied=h.to_dict()
    copied.clear()
    assert len(h.to_dict())==3

@pytest.mark.parametrize("seed",range(8))
def test_expectation_and_variance_native_oracle(seed,monkeypatch):
    rng=np.random.default_rng(seed)
    vector=rng.normal(size=8)+1j*rng.normal(size=8)
    vector/=np.linalg.norm(vector)
    r=q.Result(vector)
    coefficients=rng.normal(size=4)
    h=coefficients[0]*q.X(0)+coefficients[1]*(q.Y(0)@q.Z(2))+coefficients[2]*(q.X(1)@q.X(2))+coefficients[3]
    dense=SparsePauliOp.from_list([("IIX",coefficients[0]),("ZIY",coefficients[1]),("XXI",coefficients[2]),("III",coefficients[3])]).to_matrix()
    mean=np.vdot(vector,dense@vector).real
    variance=np.linalg.norm(dense@vector-mean*vector)**2
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("implicit simulation"))
    assert r.math.expectation(h)==pytest.approx(mean,abs=1e-12)
    assert r.math.observable(h)==pytest.approx(mean,abs=1e-12)
    assert r.math.variance(h)==pytest.approx(variance,abs=1e-12)
    assert r.math.observable_variance(h)==pytest.approx(variance,abs=1e-12)
    assert r.math.observable_variance_streamed(h)==pytest.approx(variance,abs=1e-12)
    r.test.expectation(h,mean).require()

def test_algebra_canonical_zero_and_real_scalars():
    assert (q.X(1)-q.X(1)).to_dict()=={"II":0.0}
    assert (0*q.X(1)).to_dict()=={"II":0.0}
    assert (2-q.Z(0)).to_dict()=={"I":2.0,"Z":-1.0}
    assert sum([q.X(0),q.X(0)]).to_dict()=={"X":2.0}
    assert ((q.X(0)+q.Z(0))@q.Y(1)).to_dict()=={"YX":1.0,"YZ":1.0}
    assert (q.I(2)@q.Z(0)).to_dict()=={"IIZ":1.0}
    r=q.bell().run()
    r.test.expectation(2*q.I()+q.X(0)@q.X(1),3).require()
    assert r.math.variance(2*q.I())==pytest.approx(0)
    assert r.math.expectation(0*q.X(0))==0

def test_invalid_algebra_and_budgets():
    for bad in ({},{"X":1,"II":1},{"x":1},{"X":float("nan")},{"X":True},{"X":1j}):
        with pytest.raises(ValueError):
            q.Observable(bad)
    for bad in (True,-1,1.2):
        with pytest.raises(ValueError):
            q.X(bad)
    with pytest.raises(q.ResourceLimit):
        q.X(62)
    with pytest.raises(ValueError):
        q.X(0)@q.Y(0)
    with pytest.raises(ValueError):
        q.X(0)+float("inf")
    with pytest.raises(ValueError):
        q.X(0)-True
    with pytest.raises(TypeError):
        q.X(0)*1j
    with pytest.raises(TypeError):
        q.X(0)*q.Y(1)
    with pytest.raises(q.ResourceLimit):
        q.bell().run().math.observable_variance_streamed(q.X(0),max_work=1)
    with pytest.raises(q.ResourceLimit):
        q.bell().run().math.observable_variance(q.X(0),max_bytes=1)
    with pytest.raises(ValueError):
        q.bell().run().math.expectation(q.Z(3))
    # Distinct disjoint-support terms can exceed the result cap.
    a=q.Observable({"".join(p):1 for p in itertools.product("IXYZ",repeat=4)})
    with pytest.raises(q.ResourceLimit):
        a@(q.X(4)+q.Y(4))
    with pytest.raises(q.ResourceLimit):
        a@q.Observable({"".join(p)+"IIII":1 for p in itertools.product("IXYZ",repeat=4)})
