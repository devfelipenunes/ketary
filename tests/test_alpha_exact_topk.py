import heapq
import numpy as np
import pytest
import ketary as q

def old(result,k):
    data=result._data
    ranked=heapq.nlargest(min(k,len(data)),range(len(data)),key=lambda i:(abs(data[i])**2,-i))
    return {format(i,f"0{result.num_qubits}b"):float(abs(data[i])**2/result._norm_sq) for i in ranked}

@pytest.mark.parametrize("n",[9,10,14])
@pytest.mark.parametrize("kind",["random","near_ties","sparse"])
@pytest.mark.parametrize("k",[1,7,8,16,32,33,64])
def test_exact_public_topk(n,kind,k):
    rng=np.random.default_rng(1101)
    if kind=="random":v=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    elif kind=="near_ties":v=np.exp(1j*rng.uniform(-np.pi,np.pi,size=1<<n))
    else:
        v=np.zeros(1<<n,dtype=np.complex128);v[[0,1,17,-1]]=1
    v/=np.linalg.norm(v);r=q.Result(v)
    before=r.math.statevector()
    assert list(r.math.top_probabilities(k=k).items())==list(old(r,k).items())
    np.testing.assert_array_equal(r.math.statevector(),before)

def test_exact_topk_keeps_public_limits():
    r=q.bell().run()
    assert list(r.math.top_probabilities(k=8).items())==list(old(r,8).items())
    for invalid in (0,True,1.5):
        with pytest.raises(ValueError):r.math.top_probabilities(k=invalid)
    with pytest.raises(q.ResourceLimit):r.math.top_probabilities(k=65537)
