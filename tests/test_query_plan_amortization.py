import pytest
from research.query_plan_amortization import evaluate
@pytest.mark.parametrize("n,gates",[(4,32),(8,256),(12,32)])
def test_amortized_query_plan(n,gates):
    row=evaluate(n,gates,reps=1)
    assert row["max_error"]<1e-9
    for v in row["variants"].values():
        assert len(v["run"]["raw_ms"])==16
        assert v["total_16"]["p50_ms"]>=v["total_4"]["p50_ms"]>=v["total_1"]["p50_ms"]
