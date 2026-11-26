"""CH12/13: explicit symbolic exact evolution, including relative phase."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from scipy.linalg import expm

P={"I":np.eye(2,dtype=complex),"X":np.array([[0,1],[1,0]],complex),"Y":np.array([[0,-1j],[1j,0]],complex),"Z":np.diag([1.,-1.])}
def pauli(label):
    a=np.array([[1]],complex)
    for p in label:a=np.kron(a,P[p])
    return a
def dense(terms):return sum(v*pauli(k) for k,v in terms.items())
def matrix(c):return Operator(c.to_qiskit()).data
def same(a,b):np.testing.assert_allclose(a,b,atol=1e-9,rtol=0)

@pytest.mark.parametrize("label",["I","X","Y","Z","II","XX","YY","ZZ","XZ","XYZ","YIX","IYY"])
@pytest.mark.parametrize("value",[-.37,0.,.81])
def test_symbolic_time_complete_bind_and_replay(label,value):
    n=len(label);t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(n).evolve(q.Observable({label:.7}),time=t)
    assert c.parameters==(t,)
    with pytest.raises(q.UnsupportedOperation):c.run()
    with pytest.raises(q.UnsupportedOperation):c.to_json()
    expected=expm(-.7j*value*pauli(label))
    bound=c.bind({t:value})
    same(matrix(bound),expected)
    same(matrix(q.Circuit.from_json(bound.to_json())),expected)
    assert c.parameters==(t,)

@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_symbolic_weighted_qaoa(seed):
    n=3;g,b=q.Circuit.parameter_vector("t",2)
    cost={"III":.9,"IZZ":-.5,"ZZI":-.4}
    mixer={"IIX":1.,"IXI":1.,"XII":1.}
    c=q.Circuit.symbolic(n).h(range(n)).evolve(q.Observable(cost),time=g).evolve(q.Observable(mixer),time=b)
    h=np.array([[1,1],[1,-1]])/np.sqrt(2)
    initial=np.kron(np.kron(h,h),h)
    rng=np.random.default_rng(seed);rows=rng.uniform(-1,1,(3,2))
    v=rng.normal(size=8)+1j*rng.normal(size=8);v/=np.linalg.norm(v)
    results=c.sweep_rows(rows).run()
    for row,result in zip(rows,results,strict=True):
        wanted=expm(-1j*row[1]*dense(mixer))@expm(-1j*row[0]*dense(cost))@initial
        bound=c.bind(row)
        same(matrix(bound),wanted)
        same(bound.run(initial_state=v).math.statevector(),wanted@v)
        same(result.math.statevector(),wanted[:,0])
    assert c.parameters==(g,b)

def test_shared_expression_and_phase_only_parameter():
    a,b=q.Circuit.parameter_vector("t",2)
    c=q.Circuit.symbolic(2).checkpoint("before").ry(a,0)
    c.evolve(q.I(),time=b)
    assert not c.checkpoints
    assert set(c.parameters)=={a,b}
    c.evolve(q.Z(0)@q.Z(1),time=2*a-b)
    ref=q.Circuit(2).ry(.3,0).evolve(q.I(),time=-.2).evolve(q.Z(0)@q.Z(1),time=.8)
    same(matrix(c.bind({a:.3,b:-.2})),matrix(ref))

def test_same_parameter_reuse_through_composition():
    t=q.Circuit.parameter("t")
    block=q.Circuit.symbolic(1).evolve(q.I()+q.Z(0),time=t)
    c=q.Circuit.symbolic(2).apply_each(block,placements=[(1,),(0,)])
    assert c.parameters==(t,)
    expected=expm(-.31j*(2*np.eye(4)+pauli("ZI")+pauli("IZ")))
    same(matrix(c.bind({t:.31})),expected)

def test_symbolic_preflight_and_transaction(monkeypatch):
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(2).checkpoint("before").ry(t,0);before=c.to_qiskit()
    for H,time in ((q.X(0)+q.Z(0),t),(q.Z(2),t),(q.X(0),q.Circuit.parameter("t"))):
        with pytest.raises(ValueError):c.evolve(H,time=time)
        assert c.to_qiskit()==before and c.checkpoints=={"before":0}
    original=QuantumCircuit.compose
    def fail(self,*args,**kwargs):
        original(self,*args,**kwargs)
        raise RuntimeError("injected after native compose")
    monkeypatch.setattr(QuantumCircuit,"compose",fail)
    with pytest.raises(RuntimeError):c.evolve(q.I()+q.Z(0)@q.Z(1),time=t)
    assert c.to_qiskit()==before and c.checkpoints=={"before":0}

def test_binding_rejects_nonfinite_evaluated_angles():
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(1).evolve(q.X(0),time=t*1e150)
    with pytest.raises(ValueError,match="finite real"):c.bind({t:1e200})
    assert c.parameters==(t,)

def test_numeric_zero_and_symbolic_mode():
    t=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(2).ry(t,0)
    before=c.to_qiskit()
    c.evolve(q.X(0),time=0.)
    assert c.to_qiskit()==before
    with pytest.raises(ValueError):q.Circuit(2).evolve(q.X(0),time=t)
    with pytest.raises(q.UnsupportedOperation):q.Circuit.classical(2,1).evolve(q.X(0),time=t)
