"""PERF01: immutable plan snapshots, strict report and preflight."""
import pytest
import numpy as np
import ketary as q
from research.query_plan_cost import evidence,compare_nested

@pytest.mark.parametrize("seed",[1101,2202,3303])
def test_plan_reuses_validated_snapshot(seed,monkeypatch):
    c=q.Circuit(3).h(0).cp(.3,0,2).evolve(q.I(),time=.2)
    expected=c.copy();plan=c.plan(bits=["000","111"],paulis=["ZZZ","IXY"],subsystems=[(2,0)])
    v=np.random.default_rng(seed).normal(size=8)+1j*np.random.default_rng(seed+1).normal(size=8)
    v/=np.linalg.norm(v)
    original=plan.estimate()
    reference=evidence(expected.run(initial_state=v),plan,64*1024**2)
    c.x(0);c.x(1)
    # The run path may not reconstruct the logical program.
    monkeypatch.setattr(q.Circuit,"from_json",lambda *a,**k:pytest.fail("unexpected repeated replay"))
    calls=[];run=q.Circuit.run
    def wrapped(self,*a,**k):
        calls.append(1);return run(self,*a,**k)
    monkeypatch.setattr(q.Circuit,"run",wrapped)
    for _ in range(3):
        got=plan.run(initial_state=v)
        assert compare_nested(got,reference)<1e-9
        got["estimate"]["gate_count"]=99
        got["density_matrices"][0]["real"][0][0]=99
    assert plan.estimate()==original and len(calls)==3
    with pytest.raises(q.ResourceLimit):plan.run(max_bytes=1)
    assert len(calls)==3

def test_query_plan_equality_and_replay_admission():
    c=q.bell()
    assert c.plan(bits=["00"])==c.copy().plan(bits=["00"])
    assert hash(c.plan(bits=["00"]))==hash(c.copy().plan(bits=["00"]))
    with pytest.raises(q.ResourceLimit):q.Circuit(23).plan(bits=["0"*23])
