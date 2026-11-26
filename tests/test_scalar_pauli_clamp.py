"""Scalar clamp must exactly preserve the previous finite native acceptance."""
import math
import sys
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Statevector

@pytest.mark.parametrize("value",[-sys.float_info.max,-1.000000001,-1.,-.2,-0.,0.,.2,1.,1.000000001,sys.float_info.max])
@pytest.mark.parametrize("norm_delta",[-4e-10,0.,4e-10])
def test_scalar_clamp_matches_previous(value,norm_delta,monkeypatch):
    r=q.Result(np.array([np.sqrt(1+norm_delta),0],complex))
    monkeypatch.setattr(Statevector,"expectation_value",lambda *a,**k:complex(value,0.))
    with np.errstate(over="ignore"):
        expected=float(np.clip(value/r._norm_sq,-1,1))
    got=r.math.expectation("Z")
    assert type(got) is float and got==expected
    assert math.copysign(1.,got)==math.copysign(1.,expected)

@pytest.mark.parametrize("value",[complex(float("nan"),0),complex(float("inf"),0),complex(.2,float("nan")),complex(.2,1e-5)])
def test_scalar_clamp_does_not_mask_native_fault(value,monkeypatch):
    r=q.bell().run()
    monkeypatch.setattr(Statevector,"expectation_value",lambda *a,**k:value)
    with pytest.raises(ArithmeticError,match="invalid Hermitian Pauli"):
        r.math.expectations(["XX","ZZ"])
