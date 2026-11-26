import pytest
import ketary as q

def test_qcec_real_native_equivalence():
    a=q.bell()
    assert a.test.external_equivalence(a.copy().x(0).x(0))["status"]=="PASS"
    assert a.test.external_equivalence(a.copy().z(0))["status"]=="FAIL"
