import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator

def test_shared_checks():
    r=q.bell().run()
    c=q.Contract(2,probabilities={"00":.5},expectations={"XX":1},normalized=True)
    assert c.verify(r).to_dict()["checks"]==r.verify(probabilities={"00":.5},expectations={"XX":1},normalized=True)["checks"]
    assert r.verify()["status"]=="UNSUPPORTED"

def test_metrics_distinguish_element_and_operator():
    a=q.Circuit(1)
    b=q.Circuit(1).h(0)
    m=a.test.metrics(b)
    assert m["operator_norm"]==pytest.approx(2)
    assert m["max_element_error"]<m["operator_norm"]
    assert m["process_fidelity"]==pytest.approx(0)
    assert a.test.metrics(a)["status"]=="PASS"
    assert a.test.metrics(q.Circuit(2))["status"]=="FAIL"
    assert a.test.metrics(a,max_bytes=1)["status"]=="UNSUPPORTED"
    native=a.to_qiskit()
    native.global_phase=.2
    phased=q.from_qiskit(native)
    assert a.test.metrics(phased)["status"]=="FAIL"
    assert a.test.metrics(phased,ignore_global_phase=True)["status"]=="PASS"

def test_capabilities():
    a=q.Circuit(1)
    assert a.capabilities["run_statevector"]
    t=q.Circuit.parameter("t")
    b=q.Circuit.symbolic(1).rx(t,0)
    assert not b.capabilities["run_statevector"]
    assert b.bind({t:.3}).capabilities["run_statevector"]
    assert q.Circuit.classical(1,1).capabilities["run_shots"]

@pytest.mark.parametrize("seed",range(12))
def test_streamed_variance_random(seed):
    rng=np.random.default_rng(seed)
    a=rng.normal(size=8)+1j*rng.normal(size=8)
    a/=np.linalg.norm(a)
    r=q.Result(a)
    terms={"XYZ":.3,"YYY":-.8,"IZX":.2,"III":1.5}
    assert r.math.observable_variance_streamed(terms)==pytest.approx(r.math.observable_variance(terms),abs=1e-11)

def test_streamed_resource():
    r=q.Circuit(10).h(0).run()
    assert r.math.observable_variance_streamed({"I"*9+"Z":1})==pytest.approx(1)
    with pytest.raises(q.ResourceLimit):
        r.math.observable_variance_streamed({"I"*10:1},max_work=1)
