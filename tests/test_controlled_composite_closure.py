"""Strict controlled composite operators, including phase and spectators (#282)."""
import itertools
import numpy as np
import pytest
import ketary as q
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

X=np.array([[0,1],[1,0]],complex)
Y=np.array([[0,-1j],[1j,0]],complex)
I=np.eye(2)


def analytic(theta,phase,controls,state):
    U=np.exp(1j*phase)*(np.cos(theta/2)*I-1j*np.sin(theta/2)*Y)
    out=np.eye(1<<(controls+1),dtype=complex)
    indexes=[state,state+(1<<controls)]
    out[np.ix_(indexes,indexes)]=U
    return out


@pytest.mark.parametrize("theta,phase",[(.71,.31),(-.52,-.8),(0.,.4)])
@pytest.mark.parametrize("controls,state",[(1,0),(1,1),(2,0),(2,1),(2,2),(2,3)])
def test_controlled_phase_operator(theta,phase,controls,state):
    block=q.Circuit(1).ry(theta,0).evolve(q.I(),time=-phase)
    before=block.to_qiskit()
    controlled=block.control(controls=controls,control_state=state,seed=282)
    raw=QuantumCircuit(1,global_phase=phase)
    raw.ry(theta,0)
    ref=QuantumCircuit(controls+1)
    ref.append(raw.to_gate().control(controls,ctrl_state=state,annotated=False),range(controls+1))
    expected=analytic(theta,phase,controls,state)
    np.testing.assert_allclose(Operator(controlled.to_qiskit()).data,expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose(Operator(ref).data,expected,atol=1e-9,rtol=0)
    assert block.to_qiskit()==before
    # Noncontiguous placement and occupied spectator: embed without assuming zero input.
    n=controls+2
    wires=tuple(reversed(range(1,n)))
    P=np.zeros((1<<n,1<<n),complex)
    for j in range(1<<n):
        bits=sum(((j>>k)&1)<<w for k,w in enumerate(wires))
        P[bits+((j>>(n-1))&1),j]=1
    full=P@np.kron(I,expected)@P.T
    c=q.Circuit(n).apply(controlled,wires=wires)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,full,atol=1e-9,rtol=0)
    rng=np.random.default_rng(282+state)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    v/=np.linalg.norm(v)
    np.testing.assert_allclose(c.run(initial_state=v).math.statevector(),full@v,atol=1e-9,rtol=0)


def test_control_preflight_and_source_ownership(monkeypatch):
    import ketary._transpilation as private
    monkeypatch.setattr(private,"_synthesize_native",lambda *a,**k:pytest.fail("unexpected synthesis"))
    c=q.Circuit(2).h(0).cx(0,1)
    before=c.to_qiskit()
    with pytest.raises(ValueError):
        c.control(controls=0)
    with pytest.raises(ValueError):
        c.control(controls=True)
    with pytest.raises(ValueError):
        c.control(controls=2,control_state=4)
    with pytest.raises(q.ResourceLimit):
        c.control(controls=4)
    with pytest.raises(q.UnsupportedOperation):
        q.Circuit.classical(2,2).control()
    p=q.Circuit.parameter("a")
    with pytest.raises(q.UnsupportedOperation):
        q.Circuit.symbolic(2).rx(p,0).control()
    assert c.to_qiskit()==before
