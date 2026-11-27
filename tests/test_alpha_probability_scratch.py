"""Probability scratch regression: match the previous expressions exactly."""
import numpy as np
import pytest
import ketary as q

def snapshot(n, seed, scale=1.0):
    rng=np.random.default_rng(seed)
    a=rng.normal(size=1<<n)+1j*rng.normal(size=1<<n)
    a=a/np.linalg.norm(a)*scale
    return q.Result(a)

@pytest.mark.parametrize("n,seed",[(1,13),(3,42),(6,91),(9,17)])
@pytest.mark.parametrize("scale",[1.0,1.0+2e-10])
def test_probability_buffer_matches_old_expression(n,seed,scale):
    r=snapshot(n,seed,scale)
    before=r.math.statevector()
    norm=float(np.vdot(before,before).real)
    p=np.abs(before)**2/norm
    expected={format(i,f"0{n}b"):float(v) for i,v in enumerate(p)}
    assert r.math.probabilities()==expected
    for wires in [(0,),tuple(range(n)),tuple(range(n-1,-1,-1)),tuple(range(0,n,2))]:
        axes=[n-1-w for w in wires]
        rest=[i for i in range(n) if i not in axes]
        values=p.reshape((2,)*n).transpose(axes+rest).reshape(1<<len(wires),-1).sum(axis=1)
        assert r.math.marginal_probabilities(wires)=={format(i,f"0{len(wires)}b"):float(v) for i,v in enumerate(values)}
    assert np.array_equal(r.math.statevector(),before)

@pytest.mark.parametrize("n,seed",[(1,13),(3,42),(6,91),(9,17)])
@pytest.mark.parametrize("same",[True,False])
def test_distribution_buffer_matches_old_expression(n,seed,same):
    a=snapshot(n,seed,1.0+2e-10)
    b=a if same else snapshot(n,seed+1)
    av,bv=a.math.statevector(),b.math.statevector()
    p,qv=np.abs(av)**2,np.abs(bv)**2
    expected=float(.5*np.sum(np.abs(p/p.sum()-qv/qv.sum())))
    report=a.test.distribution(b,atol=expected)
    assert report.actual==expected
    assert report.status=="PASS"
    assert np.array_equal(a.math.statevector(),av)
    assert np.array_equal(b.math.statevector(),bv)

def test_caps_before_probability_allocation(monkeypatch):
    r=snapshot(4,12)
    def fail(*args,**kwargs):
        pytest.fail("probability buffer created before admission")
    monkeypatch.setattr(np,"abs",fail)
    with pytest.raises(q.ResourceLimit):r.math.probabilities(max_outcomes=15)
    with pytest.raises(q.ResourceLimit):r.math.marginal_probabilities([3,1],max_outcomes=3)
    with pytest.raises(ValueError):r.math.marginal_probabilities([1,1])
    with pytest.raises(ValueError):r.test.distribution(r,atol=-1)
