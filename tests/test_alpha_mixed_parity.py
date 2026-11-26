import numpy as np
import pytest
import ketary as q
from qiskit.quantum_info import Operator,SparsePauliOp
from scipy.linalg import expm
from research.alpha_mixed_parity import shared,fixture,run

@pytest.mark.parametrize("n",[4,5,6])
def test_common_basis_full_operator(n):
    terms=fixture(n,1101);t=.42
    expected=expm(-1j*t*SparsePauliOp.from_list(list(terms.items())).to_matrix())
    c=shared(n,terms,t)
    np.testing.assert_allclose(Operator(c.to_qiskit()).data,expected,atol=1e-9,rtol=0)
    # Reverse logical wires, preserving Y signs and relative phase.
    p=[int(format(i,f"0{n}b")[::-1],2) for i in range(1<<n)]
    reverse=q.Circuit(n).apply(c,wires=list(reversed(range(n))))
    np.testing.assert_allclose(Operator(reverse.to_qiskit()).data,expected[np.ix_(p,p)],atol=1e-9,rtol=0)
    assert np.max(abs(expected-expected.conj()))>1e-9

def test_commuting_does_not_imply_common_local_basis():
    with pytest.raises(ValueError):shared(2,{"XX":.2,"ZZ":.3},.4)
    q.Circuit(2).evolve(q.Observable({"XX":.2,"ZZ":.3}),time=.4)

def test_profile_smoke():
    assert len(run(1101,1))==3
