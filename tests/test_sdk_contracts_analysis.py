from dataclasses import FrozenInstanceError
import numpy as np
import pytest
import ketary as q

def test_contract_is_immutable_and_explicit(monkeypatch):
    c=q.bell()
    good=c.run()
    bad=c.z(0).run()
    targets={"XX":1}
    contract=q.Contract(2,probabilities={"00":.5},expectations=targets)
    targets["XX"]=-1
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("hidden execution"))
    contract.verify(good).require()
    report=contract.verify(bad)
    assert report.status=="FAIL"
    assert report.to_dict()["checks"]["expectation:XX"]["actual"]==pytest.approx(-1)
    assert "FAIL expectation:XX" in report.render()
    with pytest.raises(FrozenInstanceError):
        contract.atol=1
    with pytest.raises(AssertionError):
        report.require()
    with pytest.raises(ValueError):
        q.Contract(2,expectations={"XX":True})
    with pytest.raises(ValueError):
        q.Contract(2)

def test_math_analytics():
    r=q.bell().run()
    assert r.math.conditional_probability({1:1},{0:1})==pytest.approx(1)
    assert r.math.conditional_probability({0:0},{0:1})==0
    with pytest.raises(ValueError):
        r.math.conditional_probability({}, {0:0,1:1})
    np.testing.assert_allclose(r.math.schmidt([0]),[1/np.sqrt(2)]*2,atol=1e-12)
    assert r.math.trace_distance(q.bell().z(0).run())==pytest.approx(1)
    assert r.math.variance("XX")==pytest.approx(0,abs=1e-12)
    assert r.math.variance("ZI")==pytest.approx(1)
    assert list(r.math.top_probabilities(k=2))==["00","11"]

def test_checkpoint_matches_trace():
    c=q.Circuit(3).h(2).cx(2,0).rz(.37,0)
    for i,step in enumerate(c.debug.trace()):
        selected=c.debug.checkpoint(i)
        assert selected.operation==step.operation
        selected.result.test.state(step.result,ignore_global_phase=False).require()
    with pytest.raises(ValueError):
        c.debug.checkpoint(4)
    with pytest.raises(q.ResourceLimit):
        c.debug.checkpoint(2,max_steps=1)
