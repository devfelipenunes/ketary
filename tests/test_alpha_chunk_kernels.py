import numpy as np
import pytest
from qiskit import QuantumCircuit
from research.alpha_chunk_kernels import topk_reference,topk_chunks,marginal_reference,marginal_chunks,wire_components
from research.alpha_chunk_profile import profile,near_ties

@pytest.mark.parametrize("chunk",[1,7,64,256])
def test_topk_exact_real_ties_and_order(chunk):
    state=np.zeros(256,dtype=complex)
    state[[0,7,63,64,127,255]]=1
    state/=np.linalg.norm(state)
    for k in (1,4,8,256):
        assert topk_chunks(state,k,chunk)==topk_reference(state,k)
        assert topk_chunks(state,k,chunk,exact=True)==topk_reference(state,k)

@pytest.mark.parametrize("wires",[(3,0),(0,3),(2,1,0),(3,2,1,0)])
def test_chunked_marginal_ordered_oracle(wires):
    rng=np.random.default_rng(1101)
    state=rng.normal(size=16)+1j*rng.normal(size=16)
    norm=float(np.vdot(state,state).real)
    expected=np.zeros(1<<len(wires))
    for i,v in enumerate(state):
        label=0
        for w in wires:label=(label<<1)|((i>>w)&1)
        expected[label]+=abs(v)**2/norm
    for chunk in (1,3,16):
        np.testing.assert_allclose(marginal_chunks(state,wires,norm,chunk),expected,atol=1e-9,rtol=0)
    np.testing.assert_allclose(marginal_reference(state,4,wires,norm),expected,atol=1e-9,rtol=0)

def test_component_partition_is_structural():
    c=QuantumCircuit(5,global_phase=.37);c.h(0);c.cx(0,2);c.cx(1,3)
    assert wire_components(c)==((0,2),(1,3),(4,))
    c.cx(2,3)
    assert wire_components(c)==((0,1,2,3),(4,))
    d=QuantumCircuit(2,2);d.measure(0,0)
    with pytest.raises(ValueError):wire_components(d)

def test_chunk_profile_smoke():
    rows=profile(1101,1,quick=True)
    assert len(rows)==3
    assert all(len(r["paths"])==(5 if r["operation"]=="topk" else 3) for r in rows)
    # Record rank disagreements instead of silently accepting a vectorized
    # kernel as a drop-in replacement; this is an experiment only.
    assert all(r["paths"]["0"]["checks"][0]["ordered_match"] is True for r in rows if r["operation"]=="topk")


def test_scalar_scores_preserve_near_ties():
    rows=near_ties()
    assert len(rows)==6 and all(r["exact_ordered_match"] for r in rows)
