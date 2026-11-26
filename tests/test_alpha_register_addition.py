import numpy as np
import pytest
from qiskit.quantum_info import Operator
from research.alpha_register_addition import sdk_add,native_add,reference,run

@pytest.mark.parametrize("n",[1,2,3])
def test_modular_register_addition(n):
    expected=reference(n)
    c=sdk_add(n)
    for raw in (c.to_qiskit(),native_add(n)):
        np.testing.assert_allclose(Operator(raw).data,expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose(Operator(c.inverse().to_qiskit()).data,expected.conj().T,atol=1e-9,rtol=0)
    # Reversed placement of the entire source block is not an identity.
    reversed_wires=list(reversed(range(2*n)))
    import ketary as q
    actual=q.Circuit(2*n).apply(c,wires=reversed_wires)
    permutation=[int(format(i,f"0{2*n}b")[::-1],2) for i in range(1<<(2*n))]
    np.testing.assert_allclose(Operator(actual.to_qiskit()).data,expected[np.ix_(permutation,permutation)],atol=1e-9,rtol=0)
    assert np.max(abs(expected-np.eye(len(expected))))>1e-9

@pytest.mark.parametrize("n",[0,4,True,1.5])
def test_research_width_boundary(n):
    with pytest.raises(ValueError):sdk_add(n)

def test_full_profile_smoke():
    assert len(run(1101,1))==3
