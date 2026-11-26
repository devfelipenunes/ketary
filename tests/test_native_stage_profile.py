import pytest
from research.native_stage_profile import evaluate
@pytest.mark.parametrize("n,layers",[(4,4),(8,16),(12,4)])
def test_native_stage_equivalence(n,layers):
    row=evaluate(n,layers,reps=3)
    assert row["max_error"]<1e-9
    assert 0<=row["adoption_count"]<=3
    assert all(len(v["raw_ms"])==3 for v in row["stages"].values())
