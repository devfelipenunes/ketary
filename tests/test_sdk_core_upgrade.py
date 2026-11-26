import json
import numpy as np
import pytest
import ketary as q

def test_direct_batch_copy_and_inspect():
    c=q.Circuit(3).h_many([0,2]).cx(0,1)
    assert c.inspect()["gate_count"]==3
    copy=c.copy().z(1)
    assert c.inspect()["gate_count"]==3 and copy.inspect()["gate_count"]==4
    with pytest.raises(ValueError):
        c.h_many([0,0])
    assert c.inspect()["gate_count"]==3

def test_explicit_initial_state():
    c=q.Circuit(2).x(0)
    assert c.run(initial_state="10").math.probability("11")==1
    assert c.run().math.probability("01")==1
    initial=q.Result([0,1,0,0])
    assert c.run(initial_state=initial).math.probability("00")==1
    assert initial.math.probability("01")==1
    np.testing.assert_allclose(c.run(initial_state=[0,0,1,0]).math.statevector(),[0,0,0,1])
    for invalid in ("2","1",[1,0]):
        with pytest.raises(ValueError):
            c.run(initial_state=invalid)

def test_reports_and_strict_numeric_validation():
    r=q.bell().run()
    assert r.verify(expectations={"XX":1,"ZZ":1})["status"]=="PASS"
    assert r.verify(expectations={"XX":-1})["status"]=="FAIL"
    assert json.loads(json.dumps(r.evidence(bits=["00"],paulis=["XX"])))["basis"]["00"]["probability"]==pytest.approx(.5)
    for invalid in ("1",True):
        with pytest.raises(ValueError):
            r.test.expectation("XX",invalid)
