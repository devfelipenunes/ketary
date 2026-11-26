import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Operator
import ketary as q

@pytest.mark.parametrize("n",[1,2,3,4])
def test_qft_exact_matrix(n):
    N=2**n
    expected=np.exp(2j*np.pi*np.outer(np.arange(N),np.arange(N))/N)/np.sqrt(N)
    c=q.qft(n)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,atol=1e-12,rtol=0)
    c.compose(q.qft(n,inverse=True)).test.equivalent(q.Circuit(n)).require()

@pytest.mark.parametrize("mask",["1","101","0110","1111"])
def test_bv(mask):
    r=q.bernstein_vazirani(mask).run()
    assert r.math.marginal_probabilities(reversed(range(len(mask))))[mask]==pytest.approx(1)

@pytest.mark.parametrize("marked",["00","01","10","11","000","101","111"])
def test_grover(marked):
    r=q.grover(marked).run()
    assert r.math.probability(marked)>.9

@pytest.mark.parametrize("bits",["00","01","10","11"])
def test_superdense(bits):
    assert q.superdense(bits).run().math.probability(bits)==pytest.approx(1)

def test_bound_template_and_sample():
    theta=Parameter("theta")
    native=QuantumCircuit(2)
    native.ry(theta,0)
    native.cx(0,1)
    c=q.Circuit.from_parameterized(native,{theta:np.pi})
    assert c.run().sample(shots=20,wires=[1,0],seed=1)=={"11":20}
    assert c.run().sample(shots=20,wires=[0],seed=1)=={"1":20}
    assert len(native.parameters)==1
    with pytest.raises(ValueError):
        q.Circuit.from_parameterized(native,{})
    with pytest.raises(ValueError):
        q.Circuit.from_parameterized(native,{theta:True})
