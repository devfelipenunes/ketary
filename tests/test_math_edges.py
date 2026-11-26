import json
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit.library import RYGate
import ketary as q

@pytest.mark.parametrize("scale",[1-8e-10,1+8e-10])
def test_near_normalized_observables(scale):
    r=q.Result([np.sqrt(scale),0])
    assert r.math.norm()==pytest.approx(np.sqrt(scale),abs=1e-15,rel=0)
    assert r.math.probability("0")==pytest.approx(1,abs=1e-14,rel=0)
    assert sum(r.math.probabilities().values())==pytest.approx(1,abs=1e-14,rel=0)
    assert r.math.marginal_probabilities([0])["0"]==pytest.approx(1,abs=1e-14,rel=0)
    assert r.math.expectation("Z")==pytest.approx(1,abs=1e-14,rel=0)

@pytest.mark.parametrize("bad",[True,"0.1",complex(1,2),float("inf"),10**400])
def test_strict_check_scalars(bad):
    r=q.bell().run()
    with pytest.raises(ValueError): r.test.normalized(atol=bad)
    with pytest.raises(ValueError): r.test.probability("00",bad)
    with pytest.raises(ValueError): r.test.fidelity(r,minimum=bad)

def test_wrong_native_and_check_types():
    with pytest.raises(TypeError): q.from_qiskit(None)
    with pytest.raises(TypeError): q.bell().test.equivalent(None)
    with pytest.raises(ValueError): q.Result([1,0]).test.state(q.bell().run())
    with pytest.raises(TypeError): q.bell().run().test.distribution(None)
    with pytest.raises(q.UnsupportedOperation): q.from_qiskit(QuantumCircuit(0))

def test_replay_malformed_producer_and_text():
    data=json.loads(q.bell().to_json()); data["producer"]["python"]=""
    with pytest.raises(ValueError): q.Circuit.from_json(json.dumps(data))
    with pytest.raises(TypeError): q.Circuit.from_json(b"{}")
    with pytest.raises(ValueError): q.Circuit.from_json("\ud800")

def test_native_gate_parameter_isolation():
    g=RYGate(.3); c=q.Circuit(1).append(g,[0]); reference=c.run()
    g.params=[.7]
    reference.test.state(c.run(),ignore_global_phase=False).require()
