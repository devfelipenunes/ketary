"""Product epic: runtime regressions for pair building, parity and verification."""
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit,transpile
from qiskit.quantum_info import Operator
from scipy.linalg import expm

@pytest.mark.parametrize("symbolic",[False,True])
def test_pair_fast_path_order_and_atomicity(symbolic):
    p=q.Circuit.parameter("p")
    c=q.Circuit.symbolic(4) if symbolic else q.Circuit(4)
    angle=p if symbolic else .31
    pairs=[(3,0),(0,2),(3,0),(2,1)]
    c.cp(angle,pairs=pairs)
    native=QuantumCircuit(4)
    for a,b in pairs:native.cp(angle,a,b)
    assert c.to_qiskit()==native
    before=c.to_qiskit()
    for invalid in ((4,0),(0,0),(True,1),(0,-1)):
        with pytest.raises(ValueError):c.cx(pairs=[(0,1),invalid])
        assert c.to_qiskit()==before
    c.cx(pairs=[(np.int64(3),np.int64(1))])
    native.cx(3,1)
    assert c.to_qiskit()==native

def dense(label):
    m=np.array([[1.]],complex)
    for axis in label:m=np.kron(m,np.eye(2) if axis=="I" else np.diag([1.,-1.]))
    return m

@pytest.mark.parametrize("symbolic",[False,True])
@pytest.mark.parametrize("t",[-.31,.72])
def test_shared_diagonal_parity(symbolic,t):
    H=q.Observable({"ZZZI":.4,"ZZIZ":-.7,"ZIZZ":.2,"IIII":.31})
    c=q.Circuit.symbolic(4) if symbolic else q.Circuit(4)
    p=q.Circuit.parameter("p")
    c.evolve(H,time=p if symbolic else t)
    if symbolic:c=c.bind({p:t})
    raw=c.to_qiskit()
    ref=expm(-1j*t*sum(coef*dense(label) for label,coef in H.to_dict().items()))
    np.testing.assert_allclose(Operator(raw).data,ref,atol=1e-9,rtol=0)
    rng=np.random.default_rng(1101);v=rng.normal(size=16)+1j*rng.normal(size=16);v/=np.linalg.norm(v)
    np.testing.assert_allclose(c.run(initial_state=v).math.statevector(),ref@v,atol=1e-9,rtol=0)
    # Three separate parity ladders require twelve CX and three RZ.
    assert raw.count_ops().get("cx",0)<12
    assert len(raw.data)<15
    common=transpile(raw,basis_gates=["u","cx"],optimization_level=0,qubits_initially_zero=False)
    np.testing.assert_allclose(Operator(common).data,ref,atol=1e-9,rtol=0)

def test_conditional_builder_rollback(monkeypatch):
    c=q.Circuit.classical(2,1).h(0).measure(0,0)
    before=c.to_qiskit()
    original=QuantumCircuit.x
    def fail(self,*a,**kw):
        original(self,*a,**kw)
        raise RuntimeError("injected")
    monkeypatch.setattr(QuantumCircuit,"x",fail)
    with pytest.raises(RuntimeError,match="injected"):c.if_x(1,0)
    assert c.to_qiskit()==before

@pytest.mark.parametrize("ignore",[False,True])
@pytest.mark.parametrize("phase",[0.,.61])
def test_comparison_overlap_and_scope(ignore,phase):
    a=q.Circuit(2).h(0).cx(0,1).evolve(q.I(),time=phase)
    b=q.bell()
    report=a.test.compare(b,inputs=["00"],complete=False,ignore_global_phase=ignore)
    row=report["samples"][0]
    assert row["fidelity"]==pytest.approx(1.)
    assert row["distribution_tv"]==pytest.approx(0.)
    expected=0. if ignore else abs(np.exp(-1j*phase)-1)
    assert row["state_l2"]==pytest.approx(expected,abs=1e-12)
    assert report.status==("FAIL" if expected>1e-9 else "INCONCLUSIVE")

def test_derivative_modes_after_shared_expression_boundary():
    p=q.Circuit.parameter("p")
    c=q.Circuit.symbolic(1).ry(p,0).ry(2*p,0)
    t=.31
    np.testing.assert_allclose(c.expectation_jacobian({p:t},[q.Z(0)]),[[-3*np.sin(3*t)]],atol=1e-9,rtol=0)
    np.testing.assert_allclose(c.expectation_hessian({p:t},[q.Z(0)]),[[[-9*np.cos(3*t)]]],atol=1e-9,rtol=0)
    np.testing.assert_allclose(c.quantum_geometric_tensor({p:t}),[[2.25]],atol=1e-9,rtol=0)
