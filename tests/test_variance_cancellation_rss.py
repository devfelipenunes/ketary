import numpy as np
import pytest
import ketary as q
from research.variance_cancellation_rss import cancellation,analytic_case

@pytest.mark.parametrize("n",[2,8,12])
@pytest.mark.parametrize("theta",[0.,1e-6,.37])
@pytest.mark.parametrize("shift",[0.,2.**16])
def test_bounded_identity_shift(n,theta,shift):
    row=cancellation(n,shift,theta)
    assert all(v["within_1e9"] for v in row["variants"].values())

def test_resource_and_nonfinite_preflight(monkeypatch):
    r,h,_,_=analytic_case(2,1.,.37)
    import ketary._result as result
    monkeypatch.setattr(result,"_accumulate_pauli_chunks",lambda *a,**k:pytest.fail("preflight before accumulation"))
    with pytest.raises(q.ResourceLimit):r.math.observable_variance_streamed(h,max_bytes=255)
    with pytest.raises(q.ResourceLimit):r.math.observable_variance_streamed(h,max_work=1)
    with pytest.raises(ValueError):r.math.observable_variance_streamed({"IZ":float("nan")})
