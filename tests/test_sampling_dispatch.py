import numpy as np
import pytest
import ketary as q
from research.sampling_dispatch import previous,evaluate

@pytest.mark.parametrize("n",[1,4,8,12])
@pytest.mark.parametrize("shots",[1,32,1024])
@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_same_seed_and_dictionary_order(n,shots,seed):
    rng=np.random.default_rng(seed);v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n);v/=np.linalg.norm(v)
    r=q.Result(v);a=previous(r,shots,seed);b=r.sample(shots=shots,seed=seed)
    assert a==b and list(a)==list(b)
    np.testing.assert_array_equal(r.math.statevector(),v)

def test_deterministic_sparse_basis_and_limit():
    r=q.Circuit(12).x(11).run()
    assert r.sample(shots=32,seed=3)=={"100000000000":32}
    with pytest.raises(q.ResourceLimit):r.sample(shots=32,max_outcomes=1)
    assert evaluate(8,32,reps=2)["identical"]
