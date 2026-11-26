"""Math and logical-resource contracts with independent small references."""
from dataclasses import FrozenInstanceError
import numpy as np
import pytest
import ketary as q

def test_born_rule_and_complex_amplitude():
    r=q.Circuit(1).gates.h(0).gates.s(0).run()
    assert r.num_qubits==1
    assert r.math.amplitude("1")==pytest.approx(1j/np.sqrt(2))
    assert r.math.probability("1")==pytest.approx(.5)
    assert r.math.probability("1")==r.math.probabilities()["1"]
    assert r.math.explain_probability("1")=="p(|1>) = |0+0.707106781187j|^2 = 0.5"

@pytest.mark.parametrize("bad",["", "0", "000", "0x", 1])
def test_invalid_basis_label(bad):
    r=q.bell().run()
    with pytest.raises(ValueError): r.math.amplitude(bad)

@pytest.mark.parametrize("label,expected",[("II",1),("XX",1),("YY",-1),("ZZ",1),("ZI",0),("IZ",0)])
def test_bell_pauli(label,expected):
    assert q.bell().run().math.expectation(label)==pytest.approx(expected,abs=1e-12)

def test_pauli_wire_order():
    r=q.Circuit(2).gates.x(0).run()
    assert r.math.expectation("IZ")==pytest.approx(-1)
    assert r.math.expectation("ZI")==pytest.approx(1)

@pytest.mark.parametrize("bad",["X","XXX","-XX","xx","AB",None])
def test_reject_pauli_label(bad):
    with pytest.raises(ValueError): q.bell().run().math.expectation(bad)

def test_independent_pauli_matrix():
    a=np.array([1,2j,-1j,3],complex); a/=np.linalg.norm(a)
    y=np.array([[0,-1j],[1j,0]]); z=np.diag([1,-1])
    expected=np.vdot(a,np.kron(y,z)@a).real
    assert q.Result(a).math.expectation("YZ")==pytest.approx(expected,abs=1e-12)

def test_resources_snapshot_and_no_execution(monkeypatch):
    c=q.Circuit(3).gates.h(0).gates.cx(0,1).gates.ccx(0,1,2)
    r=c.run()
    def fail(*args,**kwargs): raise AssertionError("unexpected circuit execution")
    monkeypatch.setattr(q.Circuit,"run",fail)
    report=c.resources.summary()
    assert isinstance(report,q.ResourceReport)
    assert (report.num_qubits,report.gate_count,report.depth)==(3,3,3)
    assert (report.two_qubit_gates,report.three_plus_qubit_gates)==(1,1)
    assert dict(report.by_gate)=={"h":1,"cx":1,"ccx":1}
    assert r.math.expectation("ZZI")==pytest.approx(1,abs=1e-12)
    drawing=c.visualize.text()
    assert "H" in drawing and c.visualize.text()==drawing
    c.gates.z(0)
    assert report.gate_count==3 and c.resources.summary().gate_count==4
    with pytest.raises(FrozenInstanceError): report.depth=0

def test_empty_resources():
    report=q.Circuit(2).resources.summary()
    assert (report.gate_count,report.depth,report.by_gate)==(0,0,())
