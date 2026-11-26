"""Every rewrite is executable and compared, including losing rewrites."""
import pytest
from research.circuit_rewrite_ladder import CASES,evaluate,metrics
@pytest.mark.parametrize("case",CASES,ids=[c[0] for c in CASES])
def test_rewrite_semantics(case):
    row=evaluate(case,reps=3)
    assert set(row["variants"])=={"scalar","fluent","intent","qiskit"}
    assert max(v["max_error"] for v in row["variants"].values())<1e-9
    assert row["shortest_ketary"] in ("scalar","fluent","intent")
    assert all(len(v["build"]["raw_ms"])==3 for v in row["variants"].values())
def test_source_metrics_are_not_verdicts():
    assert metrics("c.h(0)")["calls"]==1
    assert metrics("for i in range(3):\n if i: c.h(i)")["nesting"]==2
