"""Independent amplitude, subsystem and strict conjugation oracles (#216 #223)."""
import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator

@pytest.mark.parametrize("n",range(2,7))
def test_ghz_reduced_state(n):
    c=q.ghz(n)
    result=c.run()
    expected=np.zeros(1<<n,complex);expected[0]=expected[-1]=1/np.sqrt(2)
    np.testing.assert_allclose(result.math.statevector(),expected,atol=1e-12,rtol=0)
    for wire in (0,n-1):
        np.testing.assert_allclose(result.math.density_matrix([wire]),np.eye(2)/2,atol=1e-12,rtol=0)

@pytest.mark.parametrize("n,edges",[(3,[(0,1),(1,2)]),(3,[(0,2),(1,2)]),(4,[(0,1),(1,2),(2,3),(3,0)]),(4,[(0,1),(0,2),(0,3)]),(5,[(0,1),(2,3),(3,4)])])
def test_graph_independent_reduced_state(n,edges):
    c=q.Circuit(n).h(range(n)).cz(pairs=edges)
    result=c.run()
    expected=np.array([(-1)**sum(((i>>a)&1)*((i>>b)&1) for a,b in edges) for i in range(1<<n)])/np.sqrt(1<<n)
    np.testing.assert_allclose(result.math.statevector(),expected,atol=1e-12,rtol=0)
    # Explicit index pairs that differ only on bit zero.
    rho=np.zeros((2,2),complex)
    for i in range(0,1<<n,2):
        v=expected[i:i+2];rho+=np.outer(v,v.conj())
    np.testing.assert_allclose(result.math.density_matrix([0]),rho,atol=1e-12,rtol=0)
    before=c.to_qiskit()
    with pytest.raises(ValueError):c.cz(pairs=[(0,1),(0,0)])
    assert c.to_qiskit()==before

@pytest.mark.parametrize("theta",[.31,-.82,1.7])
def test_conjugation_arbitrary_input(theta):
    u=q.Circuit(2).h(0).cx(0,1)
    v=q.Circuit(1).rz(theta,0)
    c=q.Circuit(2).compute_action_uncompute(u,v,compute_wires=[0,1],action_wires=[1])
    H=np.array([[1,1],[1,-1]])/np.sqrt(2)
    CX=np.eye(4)[[0,3,2,1]]
    U=CX@np.kron(np.eye(2),H)
    action=np.kron(np.diag(np.exp(np.array([-1j,1j])*theta/2)),np.eye(2))
    expected=U.conj().T@action@U
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,atol=1e-9,rtol=0)
    state=np.array([1,.3j,-.2+.4j,.7]);state=state/np.linalg.norm(state)
    np.testing.assert_allclose(c.run(initial_state=state).math.statevector(),expected@state,atol=1e-9,rtol=0)
