import math
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import SparsePauliOp
from ketary._validation import _real

@pytest.mark.parametrize("seed",[1101,2202,3303])
@pytest.mark.parametrize("n",[2,4])
def test_observable_reuse_exact_legacy_and_dense(seed,n):
    rng=np.random.default_rng(seed)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    r=q.Result(v)
    terms={"".join(p):float(rng.normal()) for p in itertools.product("IXYZ",repeat=n)}
    expected=math.fsum(_real(coef)*r.math.expectation(p) for p,coef in terms.items())
    assert r.math.observable(terms)==expected
    matrix=SparsePauliOp.from_list(list(terms.items())).to_matrix()
    np.testing.assert_allclose(expected,np.vdot(v,matrix@v).real,atol=1e-9,rtol=0)
    v[:]=0
    assert r.math.observable(terms)==expected

def test_legacy_nonstring_dispatch_and_error_order():
    r=q.bell().run()
    assert r.math.observable({q.Z(0)@q.Z(1):2.})==2.
    with pytest.raises(ValueError,match="finite real"):
        r.math.observable({"bad":float("nan")})
    with pytest.raises(ValueError,match="full-width"):
        r.math.observable({"bad":1.})
