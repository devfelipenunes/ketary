"""Independent dense oracle, chunk boundaries, complex phases and negative cases."""
from itertools import product
import numpy as np
import pytest
import ketary as q
from research.chunked_pauli import variance,evaluate

P={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),"Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}
def dense(label):
    out=np.array([[1.]])
    for axis in label:out=np.kron(out,P[axis])
    return out

@pytest.mark.parametrize("label",["".join(x) for x in product("IXYZ",repeat=2)])
@pytest.mark.parametrize("chunk",[1,3,8])
def test_chunked_variance_mixed_complex(label,chunk):
    v=np.array([1,2j,-3+1j,4-2j],complex);v/=np.linalg.norm(v)
    r=q.Result(v)
    H=q.Observable({label:.7,"IZ":-.31}) if label!="IZ" else q.Observable({"IZ":.39})
    M=sum(w*dense(s) for s,w in H.to_dict().items())
    hv=M@v;d=hv-np.vdot(v,hv)*v
    np.testing.assert_allclose(variance(r,H,chunk=chunk),np.vdot(d,d).real,atol=1e-9,rtol=0)
    np.testing.assert_array_equal(r.math.statevector(),v)

def test_noncommuting_and_identity():
    H=q.Observable({"XYZ":.7,"YZX":-.2,"III":.9,"ZZX":.31})
    v=np.random.default_rng(1101).normal(size=8)+1j*np.random.default_rng(2202).normal(size=8);v/=np.linalg.norm(v)
    r=q.Result(v)
    assert variance(r,H,chunk=3)==pytest.approx(r.math.observable_variance(H),abs=1e-9)

def test_preflight_and_zero():
    r=q.bell().run();H=q.Observable({"II":0.})
    assert variance(r,H)==0
    with pytest.raises(q.ResourceLimit):variance(r,H,max_bytes=255)
    with pytest.raises(q.ResourceLimit):variance(r,H,max_work=1)
    with pytest.raises(ValueError):variance(r,H,chunk=0)
    with pytest.raises(ValueError):variance(r,q.X(2))

@pytest.mark.parametrize("n,count",[(4,4),(8,16),(12,4)])
def test_cost(n,count):
    assert evaluate(n,count,reps=3)["max_error"]<1e-9
