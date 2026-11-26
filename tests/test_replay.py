"""Replay roundtrip, malformed artifacts and concrete regression corpus."""
import json
from pathlib import Path
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import ketary as q

def test_all_gate_roundtrip_and_phase():
    raw=QuantumCircuit(3,global_phase=.37)
    raw.h(0);raw.x(1);raw.y(2);raw.z(0)
    raw.s(1);raw.sdg(2);raw.t(0);raw.tdg(1)
    raw.rx(.4,0);raw.ry(-.3,1);raw.rz(2*np.pi,2)
    raw.cx(1,0);raw.cz(2,1);raw.swap(0,2);raw.ccx(0,1,2)
    c=q.from_qiskit(raw); payload=c.to_json()
    restored=q.Circuit.from_json(payload)
    assert type(restored) is q.Circuit
    assert restored.to_json()==payload
    np.testing.assert_allclose(Operator(restored.to_qiskit()).data,Operator(raw).data,atol=1e-12,rtol=0)
    restored.gates.x(0)
    assert c.to_qiskit()==raw

def test_replay_without_execution(monkeypatch):
    c=q.bell()
    def fail(*a,**k): raise AssertionError("unexpected execution")
    monkeypatch.setattr(q.Circuit,"run",fail)
    restored=q.Circuit.from_json(c.to_json())
    assert restored.to_qiskit()==c.to_qiskit()

@pytest.mark.parametrize("key,value",[
    ("schema_version",True),("schema_version",2),("num_qubits",True),
    ("num_qubits",0),("global_phase",True),("global_phase","0.2"),
    ("global_phase",float("nan")),("producer",{}),("operations",{}),
    ("operations",[{"gate":"measure","wires":[0],"params":[]}]),
    ("operations",[{"gate":"rx","wires":[0],"params":[True]}]),
    ("operations",[{"gate":"rx","wires":[0],"params":[]}]),
    ("operations",[{"gate":"cx","wires":[0,0],"params":[]}]),
    ("operations",[{"gate":"x","wires":[True],"params":[]}]),
    ("operations",[{"gate":"x","wires":[2],"params":[]}]),
    ("operations",[{"gate":"x","wires":[0],"params":[],"extra":1}]),
])
def test_invalid_replay(key,value):
    data=json.loads(q.bell().to_json());data[key]=value
    with pytest.raises(ValueError): q.Circuit.from_json(json.dumps(data))

def test_duplicate_keys_and_limits():
    payload=q.bell().to_json()
    with pytest.raises(ValueError): q.Circuit.from_json(payload.replace('"schema_version":1','"schema_version":1,"schema_version":1'))
    with pytest.raises(ValueError): q.Circuit.from_json("["*2000+"]"*2000)
    with pytest.raises(q.ResourceLimit): q.Circuit.from_json(" "*(1024*1024+1))
    with pytest.raises(q.ResourceLimit): q.Circuit(23).to_json()
    data=json.loads(payload);data["num_qubits"]=23
    with pytest.raises(q.ResourceLimit): q.Circuit.from_json(json.dumps(data))
    data=json.loads(payload);data["operations"]=[{"gate":"x","wires":[0],"params":[]}]*10001
    with pytest.raises(q.ResourceLimit): q.Circuit.from_json(json.dumps(data))

def test_phase_regression_corpus():
    path=Path(__file__).parent/"fixtures"/"bell-relative-phase.json"
    fixture=json.loads(path.read_text(encoding="utf-8"))
    observed=q.Circuit.from_json(json.dumps(fixture["observed"])).run()
    expected=q.Circuit.from_json(json.dumps(fixture["reference"])).run()
    assert observed.test.distribution(expected).status==fixture["distribution"]
    assert observed.test.state(expected).status==fixture["state"]
    assert observed.sample(shots=128,seed=fixture["seed"])==observed.sample(shots=128,seed=fixture["seed"])
