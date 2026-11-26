import numpy as np
import pytest
import ketary as q
from ketary._validation import _real,_angle,_tol,_int,_limit
from qiskit.quantum_info import Operator
from scipy.linalg import expm

@pytest.mark.parametrize("value",[True,np.bool_(True),"0",1+0j,np.inf,-np.inf,np.nan,10**1000])
def test_invalid_real_input_categories(value):
    for validator in (_real,_angle,_tol):
        with pytest.raises(ValueError):validator(value)

@pytest.mark.parametrize("value",[0.,-.3,np.float64(.7),np.int64(2),3])
def test_angle_real_overlap_preserves_numeric_value(value):
    assert _real(value)==_angle(value)==float(value)

def test_budget_and_tolerance_are_distinct():
    assert _int(np.int64(3))==3
    for v in (True,1.0,"1"):
        with pytest.raises(ValueError):_int(v)
    assert _angle(-.1)==-.1
    with pytest.raises(ValueError):_tol(-.1)
    _limit(3,budget=128)
    with pytest.raises(q.ResourceLimit):_limit(3,budget=127)

def test_hamiltonian_modes_preserve_contract_and_phase():
    X=np.array([[0,1],[1,0]],complex);Z=np.diag([1,-1])
    h=q.X(0)+.4*q.Z(0)+.7*q.I()
    t=.37;ref=expm(-1j*t*(X+.4*Z+.7*np.eye(2)))
    c=q.Circuit(1);before=c.to_qiskit()
    with pytest.raises(q.UnsupportedOperation):c.evolve(h,time=t)
    assert c.to_qiskit()==before
    np.testing.assert_allclose(Operator(q.Circuit(1).evolve_exact(h,time=t).to_qiskit()).data,ref,atol=1e-9,rtol=0)
    errors=[]
    for steps in (1,4,16):
        m=Operator(q.Circuit(1).evolve_product(h,time=t,steps=steps,order=2).to_qiskit()).data
        errors.append(np.linalg.norm(m-ref,2))
    assert errors[2]<errors[1]<errors[0]
    # Exact commuting mode preserves an explicitly symbolic identity phase.
    p=q.Circuit.parameter("t")
    c=q.Circuit.symbolic(1).evolve(q.X(0)+.7*q.I(),time=p)
    np.testing.assert_allclose(Operator(c.bind({p:t}).to_qiskit()).data,expm(-1j*t*(X+.7*np.eye(2))),atol=1e-9,rtol=0)
