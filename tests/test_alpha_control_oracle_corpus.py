"""Independent matrix and analytic references for controlled/oracle circuits."""
import itertools
import numpy as np
import pytest
from qiskit.quantum_info import Operator
import ketary as q

@pytest.mark.parametrize("controls,state",[(1,0),(1,1),(2,0),(2,1),(2,2),(2,3)])
@pytest.mark.parametrize("phase",[-.31,.42])
def test_controlled_relative_phase(controls,state,phase):
    angle=.57
    # Source U=e^-i phase RY(angle) then Z. Control acts on low-order wires.
    ry=np.array([[np.cos(angle/2),-np.sin(angle/2)],
                 [np.sin(angle/2),np.cos(angle/2)]],complex)
    U=np.exp(-1j*phase)*np.diag([1.,-1.])@ry
    source=q.Circuit(1).ry(angle,0).z(0).evolve(q.I(),time=phase)
    before=source.to_qiskit()
    out=source.control(controls=controls,control_state=state,seed=1101)
    expected=np.eye(1<<(controls+1),dtype=complex)
    indices=[state,state+(1<<controls)]
    expected[np.ix_(indices,indices)]=U
    np.testing.assert_allclose(Operator(out.to_qiskit()).data,expected,atol=1e-9,rtol=0)
    assert source.to_qiskit()==before

@pytest.mark.parametrize("mask",["101","110","1111"])
@pytest.mark.parametrize("offset",[0,1])
def test_parity_truth_table(mask,offset):
    n=len(mask);dim=1<<(n+1)
    value=int(mask,2)
    expected=np.zeros((dim,dim),complex)
    for x in range(dim):
        bit=((x&value).bit_count()+offset)%2
        expected[x^(bit<<n),x]=1.
    oracle=q.parity_oracle(mask,offset=offset)
    np.testing.assert_allclose(Operator(oracle.to_qiskit()).data,expected,atol=1e-9,rtol=0)

@pytest.mark.parametrize("marked",[("001",),("001","110"),("000","001","010")])
@pytest.mark.parametrize("iterations",[0,1,2])
def test_amplification_analytic(marked,iterations):
    n=3;N=1<<n
    theta=np.arcsin(np.sqrt(len(marked)/N))
    oracle=q.phase_oracle(marked)
    expected=np.diag([-1 if format(k,"03b") in marked else 1 for k in range(N)])
    np.testing.assert_allclose(Operator(oracle.to_qiskit()).data,expected,atol=1e-9,rtol=0)
    result=q.amplitude_amplification(oracle,iterations=iterations).run()
    mass=sum(result.math.probability(x) for x in marked)
    np.testing.assert_allclose(mass,np.sin((2*iterations+1)*theta)**2,atol=1e-9,rtol=0)
    q.Contract(n,normalized=True).verify(result).require()
