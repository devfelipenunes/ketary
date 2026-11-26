import json
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator
from source_reader import read_source

@pytest.mark.parametrize("gate,args",[["h",[0]],["x",[0]],["y",[0]],["z",[0]],["s",[0]],["sdg",[0]],["t",[0]],["tdg",[0]],["rx",[0.37,0]],["ry",[0.37,0]],["rz",[0.37,0]],["cx",[0,1]],["cz",[0,1]],["swap",[0,1]],["ccx",[0,1,2]]])
def test_direct_alias_equivalence(gate,args):
    a,b=q.Circuit(3),q.Circuit(3)
    assert getattr(a,gate)(*args) is a
    getattr(b.gates,gate)(*args)
    np.testing.assert_allclose(Operator(a.to_qiskit()).data,Operator(b.to_qiskit()).data,atol=1e-12,rtol=0)

def test_read_pagination_no_copy_or_simulation(monkeypatch):
    c=q.Circuit(2).h(0).cx(0,1).rz(.3,1)
    def fail(*a,**kw): raise AssertionError("copy/run forbidden")
    monkeypatch.setattr(q.Circuit,"to_qiskit",fail)
    monkeypatch.setattr(q.Circuit,"run",fail)
    a=c.inspect(limit=2); b=c.inspect(start=a["next_start"],limit=2)
    assert [x["gate"] for x in a["operations"]+b["operations"]]==["h","cx","rz"]
    assert b["next_start"] is None
    a["operations"][0]["wires"][0]=99
    assert c.inspect()["operations"][0]["wires"]==[0]
    assert json.loads(json.dumps(b,allow_nan=False))==b
    with pytest.raises(q.ResourceLimit): c.inspect(limit=257)
    with pytest.raises(ValueError): c.inspect(start=4)

def test_evidence_and_batch_no_run(monkeypatch):
    r=q.bell().run()
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**kw: pytest.fail("hidden run"))
    report=r.evidence(bits=["00","11"],paulis=["ZZ","XX"])
    assert report["basis"]["00"]["probability"]==pytest.approx(.5)
    assert report["expectations"]["XX"]==pytest.approx(1)
    v=r.verify(probabilities={"00":.5,"11":.5},expectations={"ZZ":1},normalized=True)
    assert v["status"]=="PASS"
    assert r.verify(expectations={"ZZ":-1})["status"]=="FAIL"
    assert r.verify()["status"]=="UNSUPPORTED"
    assert json.loads(json.dumps(v,allow_nan=False))==v
    with pytest.raises(q.ResourceLimit): r.evidence(bits=itertools.repeat("00"))
    with pytest.raises(ValueError): r.evidence(bits=["00","00"])
    with pytest.raises(ValueError): r.verify(expectations={"ZZ":True})
    with pytest.raises(ValueError): r.test.expectation("ZZ","1")

def test_diagnosis_structured():
    a=q.bell().x(0); b=q.bell().z(0)
    d=b.debug.compare(a).to_dict()
    assert d["step_index"]==3 and d["check"]["status"]=="FAIL"
    assert d["actual_wires"]==[0]
    assert json.loads(json.dumps(d,allow_nan=False))==d

@pytest.mark.parametrize("src",[
    "import ketary as q\nc=q.Circuit(3).h(2).cx(2,0).ry(.4,1)",
    "import ketary as q\nc=q.Circuit(3).gates.h(2).gates.cx(2,0).gates.ry(.4,1)",
    "from qiskit import QuantumCircuit\nc=QuantumCircuit(3)\nc.h(2)\nc.cx(2,0)\nc.ry(.4,1)"
])
def test_source_matches_runtime_with_gate_spans(src):
    report=read_source(src); assert report["status"]=="PASS"
    c=q.Circuit(3).h(2).cx(2,0).ry(.4,1)
    for a,b in zip(report["operations"],c.inspect()["operations"],strict=True):
        assert {k:a[k] for k in b}==b
        assert src.splitlines()[a["line"]-1][a["column"]:a["end_column"]]==a["gate"]

@pytest.mark.parametrize("src",[
    "import ketary as q\nc=q.Circuit(2)\nc.h(__import__('os').system('echo never'))",
    "import ketary as q\nc=q.Circuit(2)\nfor i in range(2): c.h(i)",
    "import ketary as q\nc=q.Circuit(2)\nc.cx(0,0)",
    "import ketary as q\nc=q.Circuit(2)\nc.rx(theta,0)",
    "import ketary as q\nq=q.Circuit(2)",
    "from qiskit import QuantumCircuit\nc=QuantumCircuit(2)\nc.h(0).cx(0,1)",
    "import ketary as q\nc=q.Circuit(2)\nc.run()",
])
def test_reader_abstains(src):
    assert read_source(src)["status"]=="UNSUPPORTED"
