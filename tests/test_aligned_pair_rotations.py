"""RF02/RF03/RF23: public aligned rotation semantics and atomicity."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
GATES=("cp","crx","cry","crz","rxx","ryy","rzz")
PAIRS=((2,0),(1,2),(2,0),(0,1))
ANGLES=(.19,-.42,.63,.17)

@pytest.mark.parametrize("gate",GATES)
@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_aligned_order(gate,seed):
    raw=QuantumCircuit(3,global_phase=.37);raw.h(2)
    c=q.from_qiskit(raw)
    rng=np.random.default_rng(seed);angles=rng.uniform(-3,3,len(PAIRS))
    returned=getattr(c,gate)(iter(angles),pairs=iter(PAIRS))
    assert returned is c
    for a,(i,j) in zip(angles,PAIRS,strict=True):getattr(raw,gate)(a,i,j)
    assert c.to_qiskit()==raw
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,Operator(raw).data,atol=1e-9,rtol=0)
    assert q.Circuit.from_json(c.to_json()).to_qiskit()==raw

@pytest.mark.parametrize("gate",GATES)
def test_scalar_broadcast_preserved(gate):
    c=q.Circuit(3);getattr(c,gate)(.31,pairs=PAIRS)
    raw=QuantumCircuit(3);getattr(raw,gate)(.31,[a for a,b in PAIRS],[b for a,b in PAIRS])
    assert c.to_qiskit()==raw

@pytest.mark.parametrize("angles",[[.1],[.1,.2,.3,.4,.5],[.1,.2,.3,float("nan")],[.1,.2,.3,True],{.1,.2}, {"a":.1}, "1234"])
def test_bad_angles_preflight(angles,monkeypatch):
    c=q.Circuit(3).h(0).checkpoint("start");before=c.to_qiskit()
    def forbidden(*args,**kwargs):pytest.fail("native append before preflight")
    monkeypatch.setattr(QuantumCircuit,"cp",forbidden)
    with pytest.raises(ValueError):c.cp(angles,pairs=PAIRS)
    assert c.to_qiskit()==before and c.checkpoints=={"start":1}

def test_bounded_iterable():
    seen=[]
    def infinite():
        while True:
            seen.append(1);yield .1
    c=q.Circuit(3)
    with pytest.raises(ValueError):c.cp(infinite(),pairs=PAIRS)
    assert len(seen)==len(PAIRS)+1 and not c.to_qiskit().data
    with pytest.raises(q.ResourceLimit):c.cp(.2,pairs=itertools.repeat((0,1)))
    assert not c.to_qiskit().data

def test_symbolic_identity_and_failure():
    c=q.Circuit.symbolic(3);a,b=q.Circuit.parameter_vector("t",2)
    c.cp([a,b,a+b],pairs=PAIRS[:3])
    assert set(c.parameters)=={a,b}
    expected=QuantumCircuit(3).cp(.2,2,0)
    raw=QuantumCircuit(3);raw.cp(.2,2,0);raw.cp(.3,1,2);raw.cp(.5,2,0)
    np.testing.assert_allclose(Operator(c.bind({a:.2,b:.3}).to_qiskit()).data,Operator(raw).data,atol=1e-9,rtol=0)
    before=c.to_qiskit()
    with pytest.raises(Exception):c.cp([a,q.Circuit.parameter(a.name)],pairs=PAIRS[:2])
    assert c.to_qiskit()==before

@pytest.mark.parametrize("mode",["bound","symbolic","classical"])
def test_native_failure_rolls_back(mode,monkeypatch):
    c=q.Circuit(3) if mode=="bound" else q.Circuit.symbolic(3) if mode=="symbolic" else q.Circuit.classical(3,1)
    c.h(0);before=c.to_qiskit();original=QuantumCircuit.cp;calls=[]
    def fail(self,*a,**k):
        result=original(self,*a,**k);calls.append(1)
        if len(calls)==2:raise RuntimeError("injected after append")
        return result
    monkeypatch.setattr(QuantumCircuit,"cp",fail)
    with pytest.raises(RuntimeError):c.cp(ANGLES,pairs=PAIRS)
    assert c.to_qiskit()==before and len(calls)==2

def test_classical_aligned_gates():
    c=q.Circuit.classical(3,1).cp(ANGLES,pairs=PAIRS)
    assert len(c.to_qiskit().data)==4
