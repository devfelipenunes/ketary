"""F05.1: fail closed before a native nonfinite value becomes a verdict."""
import pytest
import ketary as q
from qiskit.quantum_info import Statevector

@pytest.mark.parametrize("value",[complex(.5,float("nan")),complex(.5,float("inf")),complex(float("nan"),0),complex(float("inf"),0),complex(.5,1e-5)])
@pytest.mark.parametrize("path",["direct","grouped","observable","assertion","contract"])
def test_malformed_native_pauli(value,path,monkeypatch):
    c=q.bell();r=c.run()
    monkeypatch.setattr(Statevector,"expectation_value",lambda *a,**k:value)
    calls={
        "direct":lambda:r.math.expectation("ZZ"),
        "grouped":lambda:r.math.expectations(["ZZ","XX"]),
        "observable":lambda:r.math.expectation(q.Z(0)@q.Z(1)),
        "assertion":lambda:r.test.expectation("ZZ",.5),
        "contract":lambda:c.contract(expectations={"ZZ":.5}).verify(r),
    }
    with pytest.raises(ArithmeticError,match="invalid Hermitian Pauli"):
        calls[path]()

def test_valid_small_imaginary_roundoff(monkeypatch):
    r=q.bell().run()
    monkeypatch.setattr(Statevector,"expectation_value",lambda *a,**k:complex(.5,1e-12))
    assert r.math.expectation("ZZ")==pytest.approx(.5)
    assert r.test.expectation("ZZ",.5).status=="PASS"
