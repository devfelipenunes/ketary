"""Bounded dense state preparation: explicit phase, ordering and extension."""
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit.library import StatePreparation
from qiskit.quantum_info import Operator, Statevector
import ketary as q

@pytest.mark.parametrize("seed",[1101,2202,3303])
@pytest.mark.parametrize("n",[1,2,3])
def test_complex_preparation(seed,n):
    rng=np.random.default_rng(seed)
    v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    v/=np.linalg.norm(v)
    original=v.copy()
    c=q.Circuit.prepare_state(v,seed=seed)
    raw=QuantumCircuit(n)
    raw.append(StatePreparation(original),range(n))
    expected=Statevector.from_instruction(raw).data
    np.testing.assert_allclose(expected,original,atol=1e-9,rtol=0)
    np.testing.assert_allclose(c.run().math.statevector(),original,atol=1e-9,rtol=0)
    U=Operator(c.to_qiskit()).data
    np.testing.assert_allclose(U.conj().T@U,np.eye(1<<n),atol=1e-9,rtol=0)
    np.testing.assert_allclose(c.copy().apply(c.inverse()).run().math.statevector(),
                               np.eye(1<<n,dtype=complex)[:,0],atol=1e-9,rtol=0)
    v[:]=0
    np.testing.assert_allclose(c.run().math.statevector(),original,atol=1e-9,rtol=0)

def test_preparation_remapped_to_nonadjacent_reversed_wires():
    v=np.array([.4,.3j,-.5,.2j],complex);v/=np.linalg.norm(v)
    block=q.Circuit.prepare_state(v,seed=1101)
    c=q.Circuit(4).x(1).apply(block,wires=[3,0])
    expected=np.zeros(16,complex)
    for i,value in enumerate(v):
        expected[2+((i&1)<<3)+((i>>1)&1)]=value
    np.testing.assert_allclose(c.run().math.statevector(),expected,atol=1e-9,rtol=0)
    q.Contract(4,normalized=True).verify(c.run()).require()

@pytest.mark.parametrize("values",[[1,1],[1,0,0],[complex(float("nan")),0],[0,0]])
def test_preparation_rejects_invalid_vectors(values):
    with pytest.raises(ValueError):
        q.Circuit.prepare_state(values)
