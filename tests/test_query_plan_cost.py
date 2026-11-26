import pytest
from research.query_plan_cost import evaluate
import ketary as q

@pytest.mark.parametrize("n,gates",[(4,32),(8,256),(12,1024)])
def test_query_plan_cost_equivalence(n,gates):
    row=evaluate(n,gates,reps=3)
    assert row["max_error"]<1e-9
    assert all(len(v["raw_ms"])==3 for v in row["stages"].values())

def test_repeated_query_plan_source_and_budget(monkeypatch):
    c=q.bell();plan=c.plan(bits=["00","11"],paulis=["XX"],subsystems=[(0,)])
    c.x(0);old=plan.run();old["evidence"]["basis"].clear()
    assert plan.run()["evidence"]["basis"]["00"]["probability"]==pytest.approx(.5)
    monkeypatch.setattr(q.Circuit,"from_json",lambda *a,**k:pytest.fail("replay before budget"))
    with pytest.raises(q.ResourceLimit):plan.run(max_bytes=127)
