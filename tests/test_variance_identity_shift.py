"""Strict identity-shift invariance on dense, chunked and legacy fallback."""
import math
import sys
import numpy as np
import pytest
import ketary as q

@pytest.mark.parametrize("n",[1,2,8,12])
@pytest.mark.parametrize("theta",[0.,1e-6,.37])
@pytest.mark.parametrize("shift",[2.**30,2.**45,-2.**45,sys.float_info.max])
def test_variance_identity_shift(n,theta,shift):
    v=np.zeros(1<<n,complex);v[:2]=[math.cos(theta/2),math.sin(theta/2)]
    r=q.Result(v);h={"I"*n:shift,"I"*(n-1)+"Z":1.}
    expected=math.sin(theta)**2
    assert r.math.observable_variance_streamed(h)==pytest.approx(expected,abs=1e-12,rel=0)
    assert r.math.observable_variance_streamed(h,max_bytes=64*len(v))==pytest.approx(expected,abs=1e-12,rel=0)
    if n<=8:assert r.math.observable_variance(h)==pytest.approx(expected,abs=1e-12,rel=0)
    np.testing.assert_array_equal(r.math.statevector(),v)

def test_identity_only_preflight_stays_strict():
    r=q.bell().run()
    for method in (r.math.observable_variance,r.math.observable_variance_streamed):
        assert method({"II":sys.float_info.max})==0.
        with pytest.raises(ValueError):method({"II":float("inf")})
        with pytest.raises(ValueError):method({"II":1.,"XX":float("nan")})
        with pytest.raises(q.ResourceLimit):method({"II":1.},max_bytes=1)
    with pytest.raises(q.ResourceLimit):r.math.observable_variance_streamed({"II":1.},max_work=1)

def test_centered_noncommuting_dense_oracle():
    v=np.array([1,2j,3-1j,-4+2j],complex);v/=np.linalg.norm(v)
    r=q.Result(v)
    X=np.array([[0,1],[1,0]]);Y=np.array([[0,-1j],[1j,0]]);Z=np.diag([1,-1])
    m=.7*np.kron(X,Y)-.31*np.kron(Z,X)
    hv=m@v;d=hv-np.vdot(v,hv)*v
    expected=float(np.vdot(d,d).real)
    h=q.Observable({"XY":.7,"ZX":-.31,"II":2.**45})
    assert r.math.observable_variance(h)==pytest.approx(expected,abs=1e-12,rel=0)
    assert r.math.variance(h)==pytest.approx(expected,abs=1e-12,rel=0)
