"""RF07–09: public exact evolution, analytic matrices and transaction semantics."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from scipy.linalg import expm

def pauli(label):
    matrices={"I":np.eye(2),"X":np.array([[0,1],[1,0]]),"Y":np.array([[0,-1j],[1j,0]]),"Z":np.diag([1,-1])}
    out=np.array([[1.]])
    for x in label:out=np.kron(out,matrices[x])
    return out
def matrix(c):return Operator(c.to_qiskit()).data

@pytest.mark.parametrize("label",["I","X","Y","Z","II","XX","YY","ZZ","XZ","YIX","XYZ","ZZZ","IYY","XYIY"])
@pytest.mark.parametrize("t",[-.31,0.,.83])
def test_single_term_exact_phase(label,t):
    n=len(label);c=q.Circuit(n).h(0);before=matrix(c)
    H=q.Observable({label:-.7})
    assert c.evolve(H,time=t) is c
    expected=expm(.7j*t*pauli(label))@before
    np.testing.assert_allclose(matrix(c),expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose(matrix(q.Circuit.from_json(c.to_json())),expected,atol=1e-9,rtol=0)
    rng=np.random.default_rng(1101);v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    np.testing.assert_allclose(c.run(initial_state=v).math.statevector(),expected@v,atol=1e-9,rtol=0)

@pytest.mark.parametrize("t",[-.31,0.,.7])
def test_commuting_nontrivial_and_identity(t):
    terms={"XX":.7,"YY":-.31,"ZZ":.21,"II":.9}
    h=sum(v*pauli(k) for k,v in terms.items())
    c=q.Circuit(3).evolve(q.Observable(terms),time=t)
    np.testing.assert_allclose(matrix(c),expm(-1j*t*np.kron(np.eye(2),h)),atol=1e-9,rtol=0)

def test_weighted_maxcut_native_gate_count_and_phase():
    H=q.maxcut_hamiltonian(3,[(0,1),(1,2)],weights=[.5,1.2])
    c=q.Circuit(3).evolve(H,time=.3)
    assert [item.operation.name for item in c.to_qiskit().data]==["rzz","rzz"]
    h=sum(v*pauli(k) for k,v in H.to_dict().items())
    np.testing.assert_allclose(matrix(c),expm(-.3j*h),atol=1e-9,rtol=0)

def test_checkpoint_phase_and_zero_noop():
    c=q.Circuit(2).h(0).checkpoint("h")
    c.evolve(q.X(0),time=0)
    assert c.checkpoints=={"h":1}
    c.evolve(q.X(0),time=.1)
    assert c.checkpoints=={"h":1}
    c.evolve(q.I(),time=.1)
    assert c.checkpoints=={}

@pytest.mark.parametrize("H,t",[(q.X(0)+q.Z(0),.2),(q.Z(2),.2),(q.X(0),float("inf")),(q.X(0),True),(1e308*q.X(0),1e308)])
def test_invalid_preflight_no_native_append(H,t,monkeypatch):
    c=q.Circuit(2).h(0).checkpoint("before");before=c.to_qiskit()
    def forbidden(*a,**k):pytest.fail("native append before preflight")
    monkeypatch.setattr(QuantumCircuit,"compose",forbidden)
    with pytest.raises(ValueError):c.evolve(H,time=t)
    assert c.to_qiskit()==before and c.checkpoints=={"before":1}

def test_no_hidden_simulation_and_native_failure(monkeypatch):
    c=q.Circuit(2).h(0).checkpoint("before");before=c.to_qiskit()
    monkeypatch.setattr(q.Circuit,"run",lambda *a,**k:pytest.fail("implicit execution"))
    original=QuantumCircuit.compose
    def fail(self,*a,**k):
        original(self,*a,**k)
        raise RuntimeError("injected after compose")
    monkeypatch.setattr(QuantumCircuit,"compose",fail)
    with pytest.raises(RuntimeError):c.evolve(q.I()+q.Z(0)@q.Z(1),time=.2)
    assert c.to_qiskit()==before and c.checkpoints=={"before":1}

def test_modes_and_width():
    with pytest.raises(TypeError):q.Circuit(2).evolve("ZZ",time=.3)
    with pytest.raises(q.ResourceLimit):q.Circuit(9).evolve(q.X(0),time=.3)
    with pytest.raises(q.UnsupportedOperation):q.Circuit.classical(2,1).evolve(q.X(0),time=.3)
    t=q.Circuit.parameter("t")
    with pytest.raises(q.UnsupportedOperation):q.Circuit.symbolic(2).ry(t,0).evolve(q.X(0),time=.3)
