import itertools
import json
import xml.etree.ElementTree as ET
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit


@pytest.mark.parametrize("kwargs,error",[
    ({"probabilities":[]},TypeError),
    ({"probabilities":{format(i,"06b"):0 for i in range(33)}},q.ResourceLimit),
    ({"probabilities":{"0":1}},ValueError),
    ({"probabilities":{"000000":1.2}},ValueError),
    ({"expectations":{"IIIIIX":-2}},ValueError),
    ({"normalized":1},ValueError),
    ({"probabilities":{format(i,"06b"):0 for i in range(32)},"normalized":True},q.ResourceLimit),
])
def test_contract_limits(kwargs,error):
    with pytest.raises(error):
        q.Contract(6,**kwargs)


def test_contract_and_report_shapes():
    with pytest.raises(q.ResourceLimit):
        q.Contract(23,normalized=True)
    c=q.Contract(2,normalized=True)
    with pytest.raises(TypeError):
        c.verify(q.Circuit(2))
    with pytest.raises(ValueError):
        c.verify(q.Circuit(1).run())
    r=c.verify(q.bell().run()).require()
    assert r.to_dict()["checks"]["normalized"]["status"]=="PASS"
    assert r.to_dict()["scope"].endswith("not operator equivalence")
    assert "PASS" in r.render()


def test_inspection_and_evidence_guards():
    c=q.Circuit(2).h(0).cx(0,1).rz(.3,0)
    assert c.inspect(limit=1)["next_start"]==1
    assert c.inspect(start=3)["operations"]==[]
    with pytest.raises(ValueError):
        c.inspect(start=4)
    with pytest.raises(q.ResourceLimit):
        c.inspect(limit=257)
    r=c.run()
    for bits in ("00",["00","00"],[0]):
        with pytest.raises(ValueError):
            r.evidence(bits=bits)
    with pytest.raises(q.ResourceLimit):
        r.evidence(bits=itertools.repeat("00"))
    with pytest.raises(TypeError):
        r.verify(probabilities=[])
    with pytest.raises(ValueError):
        r.verify(normalized=1)
    with pytest.raises(q.ResourceLimit):
        q.Circuit(5).run().verify(probabilities={format(i,"05b"):0 for i in range(32)},normalized=True)
    assert r.verify()["status"]=="UNSUPPORTED"
    assert r.verify(normalized=True)["status"]=="PASS"


@pytest.mark.parametrize("wires",[[],[0,0],[2],itertools.repeat(0)])
def test_density_validation(wires):
    with pytest.raises(ValueError):
        q.bell().run().math.density_matrix(wires)


def test_queries_invalid_and_bounded():
    r=q.bell().run()
    for wires in ([],[0,1],[2],[0,0],itertools.repeat(0)):
        with pytest.raises(ValueError):
            r.math.schmidt(wires)
    with pytest.raises(q.ResourceLimit):
        r.math.schmidt([0],max_rank=1)
    for event in ([],{2:1},{0:2},{0:True}):
        with pytest.raises(ValueError):
            r.math.conditional_probability(event,{})
    assert r.math.conditional_probability({}, {})==1
    assert r.math.conditional_probability({0:0},{})==pytest.approx(.5)
    with pytest.raises(q.ResourceLimit):
        r.math.top_probabilities(k=65537)
    for terms in ({},[],{"XX":True},{"X":1}):
        with pytest.raises(ValueError):
            r.math.observable(terms)
    assert r.math.dirac(max_terms=1).endswith("...")
    assert r.math.dirac(atol=1)=="no terms above tolerance"
    with pytest.raises(ValueError):
        r.math.fidelity([1,0])
    with pytest.raises(ValueError):
        r.test.probability("00",1.5)
    with pytest.raises(ValueError):
        r.test.fidelity(r,minimum=-1)
    with pytest.raises(ValueError):
        r.test.expectation("XX",2)
    with pytest.raises(ValueError):
        r.math.marginal_probabilities(itertools.repeat(0))
    with pytest.raises(ValueError):
        r.math.entropy((itertools.repeat(0),[1]))
    assert q.Circuit(2).run().sample(shots=3,wires=[0])=={"0":3}


def test_algorithm_bounds_and_options():
    with pytest.raises(q.ResourceLimit):
        q.qft(23)
    with pytest.raises(ValueError):
        q.qft(2,swaps=1)
    q.qft(2,swaps=False).compose(q.qft(2,swaps=False,inverse=True)).test.equivalent(q.Circuit(2)).require()
    with pytest.raises(ValueError):
        q.grover("2")
    with pytest.raises(q.ResourceLimit):
        q.grover("00",iterations=65)
    assert q.grover("00",iterations=0).run().math.probability("00")==pytest.approx(.25)
    with pytest.raises(ValueError):
        q.superdense("x1")
    for phase in (-.1,1,True):
        with pytest.raises(ValueError):
            q.phase_estimation(phase)
    with pytest.raises(q.ResourceLimit):
        q.phase_estimation(.2,13)
    for mask in ("","00","21"):
        with pytest.raises(ValueError):
            q.simon(mask)
    with pytest.raises(q.ResourceLimit):
        q.simon("1"*11)
    with pytest.raises(ValueError):
        q.parity_oracle("1",offset=2)


def test_aliases_and_mcx_optimization():
    c=q.Circuit(3).y(0).s(0).sdg(1).t(2).tdg(0).swap(0,2).rx(.2,0).ry(.3,1).rz(.4,2).cz(1,2).ccx(0,1,2)
    assert c.inspect()["gate_count"]==11
    d=q.Circuit(4).mcx([0,1,2],3).mcx([0,1,2],3)
    assert d.optimize().inspect()["gate_count"]==0
    d.test.equivalent(d.optimize()).require()
    with pytest.raises(TypeError):
        q.Circuit.from_parameterized(None,{})
    with pytest.raises(ValueError):
        q.Circuit(1).rx(10**400,0)
    with pytest.raises(ValueError):
        q.bell().transpile(basis_gates=["h","cx"],seed=2**32)


def test_svg_schema_and_limits(monkeypatch):
    c=q.Circuit(3).h(2).cx(2,0).cp(.4,0,1)
    r=c.run()
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("hidden execution"))
    xml=c.visualize.svg()
    assert ET.fromstring(xml).tag.endswith("svg")
    assert "CX:0" in xml and "CX:1" in xml and "0.4" in xml
    assert ET.fromstring(r.visualize.bloch_svg(0)).tag.endswith("svg")
    assert "x =" in r.visualize.bloch_svg()
    with pytest.raises(q.ResourceLimit):
        c.visualize.svg(max_gates=2)
    with pytest.raises(q.ResourceLimit):
        c.visualize.svg(max_qubits=13)
    with pytest.raises(q.UnsupportedOperation):
        q.Circuit.classical(1,1).visualize.svg()
