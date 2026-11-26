import itertools
import numpy as np
import pytest
import ketary as q
from ketary._observable import _pauli_masks,_pauli_anticommutes
from qiskit.quantum_info import SparsePauliOp

def test_mask_commutation_exhaustive():
    labels=["".join(p) for p in itertools.product("IXYZ",repeat=3)]
    masks={p:_pauli_masks(p) for p in labels}
    for a,b in itertools.product(labels,repeat=2):
        assert _pauli_anticommutes(masks[a],masks[b])==bool(sum(x!="I" and y!="I" and x!=y for x,y in zip(a,b,strict=True))%2)

@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_commutation_filter_mixed_width(seed):
    rng=np.random.default_rng(seed)
    a=q.Observable({"".join(p):float(rng.normal()) for p in itertools.product("IXYZ",repeat=2)})
    b=q.Observable({"".join(p):float(rng.normal()) for p in itertools.product("IXYZ",repeat=3)})
    A=SparsePauliOp.from_list(list(a.to_dict(3).items())).to_matrix()
    B=SparsePauliOp.from_list(list(b.to_dict(3).items())).to_matrix()
    np.testing.assert_allclose(a.commutator(b).to_matrix(),A@B-B@A,atol=1e-9,rtol=0)
    np.testing.assert_allclose(a.anticommutator(b).to_qiskit(3).to_matrix(),A@B+B@A,atol=1e-9,rtol=0)

def test_exact_zero_skips_coefficient_overflow():
    a=q.Observable({"ZZ":1e200})
    assert a.commutator(a).to_list()==[("II",0j)]
    b=q.Observable({"XI":1e200})
    assert a.anticommutator(b).to_dict(2)=={"II":0.}
